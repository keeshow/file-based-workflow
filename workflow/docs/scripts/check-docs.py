#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档一致性校验。

检查 Task、Debug、Note、Handoff 及两份索引是否符合 AGENTS.md 的命名、状态和链接约定。
只读取文件，不修改任何内容；`.example` 示例文件不参与检查。

用法（在项目根目录执行）：
    python docs/scripts/check-docs.py [--root 项目根目录] [--json]

退出码：0 通过；1 有错误；2 只有警告；3 脚本无法完成检查。
需要 Python 3.7 及以上版本，只使用标准库。
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import unquote

TASK_STATUSES = ("TODO", "IN_PROGRESS", "BLOCKED", "PAUSED", "DONE", "CANCELLED")
DEBUG_STATUSES = ("排查中", "已定位", "已解决", "暂停")
SIZE_LIMITS = {"task": 4000, "debug": 6000, "handoff": 3000}

TASK_NAME_RE = re.compile(r"^(\d{3,})-.+\.md$")
NOTE_NAME_RE = re.compile(r"^(debug|note)-(\d{3,})-.+\.md$")
FIELD_RE = r"^[>\s*]*{0}[*\s]*[：:]\s*(.*)$"
STATUS_RE = re.compile(FIELD_RE.format("状态"))
AUTH_RE = re.compile(FIELD_RE.format("授权"))
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
TASK_TOKEN_RE = re.compile(r"\b(" + "|".join(TASK_STATUSES) + r")\b")
SECRET_RE = re.compile(
    r"(密码|口令|密钥|令牌|token|secret|api[_-]?key|password|passwd)\s*[：:=]\s*(\S+)",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"^(<[^>]*>|\*+|x+|…+|\.{3,}|无|略|示例)[，。；,.;]?$", re.IGNORECASE)


class ArgError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    # 参数错误改用退出码 3，避免与“只有警告”的退出码 2 混淆
    def error(self, message):
        raise ArgError(message)


class Finding:
    def __init__(self, level, code, path, line, message):
        self.level = level      # error | warning
        self.code = code
        self.path = path        # 相对项目根目录，使用 /
        self.line = line        # 行号，无则为 None
        self.message = message

    def where(self):
        return self.path if self.line is None else "{}:{}".format(self.path, self.line)

    def to_dict(self):
        return {"level": self.level, "code": self.code, "path": self.path,
                "line": self.line, "message": self.message}


class Doc:
    """一个 Markdown 文件：原始行、去除代码块后的行及解析结果。"""

    def __init__(self, root, path):
        self.root = root
        self.path = path
        self.rel = rel_path(root, path)
        with open(path, encoding="utf-8-sig") as fh:
            self.text = fh.read()
        self.lines = self.text.splitlines()
        self.prose = []          # (行号, 去除行内代码后的文本)，跳过围栏代码块
        in_fence = False
        for i, ln in enumerate(self.lines, 1):
            if FENCE_RE.match(ln):
                in_fence = not in_fence
                continue
            if not in_fence:
                self.prose.append((i, INLINE_CODE_RE.sub("", ln)))

    def field(self, regex):
        """返回第一处字段行的 (行号, 值)，值已去除 Markdown 强调符号。"""
        for i, ln in enumerate(self.lines, 1):
            m = regex.match(ln)
            if m:
                return i, m.group(1).replace("`", "").replace("*", "").strip()
        return None, None

    def size(self):
        return len(re.sub(r"\s", "", self.text))

    def links(self):
        """返回 (行号, 原始目标, 解析后的绝对路径)；外部链接和页内锚点不返回。"""
        out = []
        for i, ln in self.prose:
            for m in LINK_RE.finditer(ln):
                raw = m.group(1).strip("<>").strip()
                target = unquote(raw.split("#", 1)[0].split("?", 1)[0])
                if not target or SCHEME_RE.match(target):
                    continue
                abs_p = os.path.normpath(os.path.join(os.path.dirname(self.path), target))
                out.append((i, raw, abs_p))
        return out


def rel_path(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def same_path(a, b):
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def list_md(folder):
    """列出目录下（不含子目录）的 .md 文件，排除 README.md 和示例文件。"""
    if not os.path.isdir(folder):
        return []
    names = sorted(os.listdir(folder))
    return [os.path.join(folder, n) for n in names
            if n.endswith(".md") and n.lower() != "readme.md"
            and os.path.isfile(os.path.join(folder, n))]


class Checker:
    def __init__(self, root):
        self.root = root
        self.docs_dir = os.path.join(root, "docs")
        self.tasks_dir = os.path.join(self.docs_dir, "tasks")
        self.notes_dir = os.path.join(self.docs_dir, "notes")
        self.findings = []
        self.tasks = {}      # 绝对路径 -> {"doc", "status"}
        self.notes = {}      # 绝对路径 -> {"doc", "kind", "status"}
        self.cache = {}

    def add(self, level, code, path, line, message):
        self.findings.append(Finding(level, code, path, line, message))

    def load(self, path):
        """读取文件；无法按 UTF-8 读取时记一条警告并返回 None。"""
        key = os.path.normcase(os.path.abspath(path))
        if key not in self.cache:
            try:
                self.cache[key] = Doc(self.root, path)
            except UnicodeDecodeError:
                self.add("warning", "READ", rel_path(self.root, path), None,
                         "无法按 UTF-8 读取，已跳过该文件的检查")
                self.cache[key] = None
        return self.cache[key]

    # ---------- Task ----------
    def check_tasks(self):
        seen = {}
        for path in list_md(self.tasks_dir):
            doc = self.load(path)
            if doc is None:
                continue
            name = os.path.basename(path)
            m = TASK_NAME_RE.match(name)
            if not m:
                self.add("error", "TASK-NAME", doc.rel, None,
                         "文件名应为“三位编号-名称.md”，如 001-download.md（AGENTS.md 第 4 节）")
            else:
                num = m.group(1)
                if num in seen:
                    self.add("error", "TASK-DUP", doc.rel, None,
                             "编号 {} 与 {} 重复，编号须唯一、稳定".format(num, seen[num]))
                else:
                    seen[num] = doc.rel
            line, value = doc.field(STATUS_RE)
            status = None
            if line is None:
                self.add("error", "TASK-STATUS", doc.rel, None,
                         "缺少以“状态：”开头的状态行")
            else:
                token = re.match(r"[A-Z_]*", value).group(0)
                if token in TASK_STATUSES:
                    status = token
                else:
                    self.add("error", "TASK-STATUS", doc.rel, line,
                             "状态行应以以下状态值开头：" + " / ".join(TASK_STATUSES))
            self.tasks[path] = {"doc": doc, "status": status}
            if status == "DONE":
                self.check_done(doc)
            self.check_size(doc, "task", "Task")

    def check_done(self, doc):
        section, level = [], None
        for i, ln in doc.prose:
            h = HEADING_RE.match(ln)
            if h:
                if level is not None and len(h.group(1)) <= level:
                    break
                if level is None and "验收" in h.group(2):
                    level = len(h.group(1))
                    continue
            if level is not None:
                section.append(ln)
        if level is None:
            self.add("warning", "TASK-DONE", doc.rel, None,
                     "状态为 DONE，但未找到验收部分，请核对是否满足已约定的验收标准")
            return
        body = "\n".join(section)
        for word in ("未通过", "未验证"):
            if word in body:
                self.add("warning", "TASK-DONE", doc.rel, None,
                         "状态为 DONE，但验收部分含“{}”，请核对验收结果".format(word))

    # ---------- Debug / Note ----------
    def check_notes(self):
        seen = {}
        for path in list_md(self.notes_dir):
            doc = self.load(path)
            if doc is None:
                continue
            m = NOTE_NAME_RE.match(os.path.basename(path))
            kind = m.group(1) if m else None
            if not m:
                self.add("error", "NOTE-NAME", doc.rel, None,
                         "文件名应为 debug-NNN-主题.md 或 note-NNN-主题.md（AGENTS.md 第 2 节）")
            else:
                num = m.group(2)
                if num in seen:
                    self.add("error", "NOTE-DUP", doc.rel, None,
                             "编号 {} 与 {} 重复；Debug 与 Note 共用一个编号序列".format(num, seen[num]))
                else:
                    seen[num] = doc.rel
            status = None
            if kind == "debug":
                line, value = doc.field(STATUS_RE)
                if line is None:
                    self.add("error", "DEBUG-STATUS", doc.rel, None,
                             "缺少以“状态：”开头的状态行")
                else:
                    status = next((s for s in DEBUG_STATUSES if value.startswith(s)), None)
                    if status is None:
                        self.add("error", "DEBUG-STATUS", doc.rel, line,
                                 "状态行应以以下状态开头：" + " / ".join(DEBUG_STATUSES))
                self.check_size(doc, "debug", "Debug")
            elif kind == "note":
                line, value = doc.field(AUTH_RE)
                if line is None or not value:
                    self.add("error", "NOTE-AUTH", doc.rel, None,
                             "缺少“授权：”行，须写明授权方式和时间（AGENTS.md 第 6 节）")
            self.notes[path] = {"doc": doc, "kind": kind, "status": status}

    # ---------- 索引 ----------
    def index_rows(self, doc, folder):
        """返回索引表格中指向 folder 内文件的行：(行号, 目标路径, 单元格列表)。"""
        rows = []
        links = {}
        for i, raw, abs_p in doc.links():
            links.setdefault(i, []).append(abs_p)
        for i, ln in doc.prose:
            s = ln.strip()
            if not s.startswith("|"):
                continue
            targets = [p for p in links.get(i, []) if same_path(os.path.dirname(p), folder)]
            if not targets:
                continue
            cells = [c.replace("`", "").replace("*", "").strip()
                     for c in s.strip("|").split("|")]
            rows.append((i, targets[0], cells))
        return rows

    def check_index(self, index_name, folder, items, code, statuses, label):
        index_path = os.path.join(folder, "README.md")
        if not items and not os.path.isfile(index_path):
            return
        if not os.path.isfile(index_path):
            self.add("error", code, rel_path(self.root, index_path), None,
                     "{}不存在，但目录中已有文档".format(index_name))
            return
        doc = self.load(index_path)
        if doc is None:
            return
        listed = set()
        for line, target, cells in self.index_rows(doc, folder):
            key = os.path.normcase(target)
            if key in listed:
                self.add("error", code, doc.rel, line,
                         "{} 在索引中重复列出".format(os.path.basename(target)))
            listed.add(key)
            item = next((v for p, v in items.items() if same_path(p, target)), None)
            if item is None or item["status"] is None:
                continue   # 目标不存在由链接检查报告；文档自身状态错误已单独报告
            row_status = None
            for c in cells:
                row_status = next((s for s in statuses if c == s or c.startswith(s)), None)
                if row_status:
                    break
            if row_status is None:
                self.add("error", code, doc.rel, line,
                         "{} 所在行缺少状态".format(os.path.basename(target)))
            elif row_status != item["status"]:
                self.add("error", code, doc.rel, line,
                         "{} 在索引中为 {}，文档中为 {}，以文档为准同步".format(
                             os.path.basename(target), row_status, item["status"]))
        for path, item in items.items():
            if os.path.normcase(path) not in listed:
                self.add("error", code, item["doc"].rel, None,
                         "未列入{}（{}）".format(index_name, label))

    # ---------- Handoff ----------
    def check_handoff(self):
        path = os.path.join(self.docs_dir, "handoff.md")
        if not os.path.isfile(path):
            return
        doc = self.load(path)
        if doc is None:
            return
        line_links = {}
        for i, raw, abs_p in doc.links():
            if same_path(os.path.dirname(abs_p), self.tasks_dir):
                line_links.setdefault(i, []).append(abs_p)
        for i, ln in doc.prose:
            targets = line_links.get(i, [])
            tokens = set(TASK_TOKEN_RE.findall(ln))
            if len(targets) != 1 or len(tokens) != 1:
                continue   # 一行涉及多个 Task 或多个状态时无法可靠对应，不检查
            item = next((v for p, v in self.tasks.items() if same_path(p, targets[0])), None)
            said = tokens.pop()
            if item and item["status"] and said != item["status"]:
                self.add("error", "HANDOFF-STATUS", doc.rel, i,
                         "{} 在 Handoff 中为 {}，Task 中为 {}，核实后同步".format(
                             os.path.basename(targets[0]), said, item["status"]))
        self.check_size(doc, "handoff", "Handoff")

    # ---------- 篇幅、链接、敏感信息 ----------
    def check_size(self, doc, kind, label):
        n = doc.size()
        if n > SIZE_LIMITS[kind]:
            self.add("warning", "SIZE", doc.rel, None,
                     "约 {} 字，超过 {} 参考篇幅 {} 字，检查是否需要整理".format(
                         n, label, SIZE_LIMITS[kind]))

    def all_docs(self):
        out = []
        for dirpath, dirs, files in os.walk(self.docs_dir):
            dirs.sort()
            for f in sorted(files):
                if f.endswith(".md"):
                    doc = self.load(os.path.join(dirpath, f))
                    if doc is not None:
                        out.append(doc)
        return out

    def check_links_and_secrets(self):
        for doc in self.all_docs():
            for i, raw, abs_p in doc.links():
                if not os.path.exists(abs_p):
                    self.add("error", "LINK", doc.rel, i, "链接目标不存在：" + raw)
            for i, ln in doc.prose:
                for m in SECRET_RE.finditer(ln):
                    if not PLACEHOLDER_RE.match(m.group(2)):
                        self.add("warning", "SECRET", doc.rel, i,
                                 "疑似记录了{}，文档中不得写入密码、密钥或令牌（AGENTS.md 第 8 节）".format(
                                     m.group(1)))
                        break

    def run(self):
        self.check_tasks()
        self.check_notes()
        self.check_index("任务总览", self.tasks_dir, self.tasks, "TASK-INDEX",
                         TASK_STATUSES, "docs/tasks/README.md")
        debug_items = {p: v for p, v in self.notes.items() if v["kind"] is not None}
        self.check_index("排查记录与专题笔记索引", self.notes_dir, debug_items, "NOTE-INDEX",
                         DEBUG_STATUSES, "docs/notes/README.md")
        self.check_handoff()
        self.check_links_and_secrets()


def main(argv=None):
    # 输出到管道时（Agent 调用的常见情况）默认使用 UTF-8；终端输出及已设置 PYTHONIOENCODING 时不改编码
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            if not os.environ.get("PYTHONIOENCODING") and not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace")
            else:
                stream.reconfigure(errors="replace")
    parser = Parser(description="检查工作流文档的命名、状态、索引和链接是否一致（只读）")
    parser.add_argument("--root", help="项目根目录；默认为本脚本所在 docs/scripts/ 的上两级目录")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    try:
        args = parser.parse_args(argv)
        root = os.path.abspath(args.root or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        if not os.path.isdir(os.path.join(root, "docs")):
            raise ArgError("未找到 {}，请用 --root 指定项目根目录".format(os.path.join(root, "docs")))
        checker = Checker(root)
        checker.run()
    except ArgError as e:
        print("[脚本错误] " + str(e), file=sys.stderr)
        return 3
    except Exception as e:  # 脚本自身问题不应影响任务结束，交由 Agent 报告
        print("[脚本错误] {}: {}".format(type(e).__name__, e), file=sys.stderr)
        return 3

    findings = checker.findings
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    code = 1 if errors else (2 if warnings else 0)
    if args.json:
        print(json.dumps({
            "root": root,
            "counts": {"task": len(checker.tasks),
                       "debug": sum(1 for v in checker.notes.values() if v["kind"] == "debug"),
                       "note": sum(1 for v in checker.notes.values() if v["kind"] == "note")},
            "errors": len(errors), "warnings": len(warnings), "exit_code": code,
            "findings": [f.to_dict() for f in errors + warnings],
        }, ensure_ascii=False, indent=2))
        return code
    print("文档校验：" + root)
    print("检查对象：Task {} 个，Debug 与 Note {} 个".format(len(checker.tasks), len(checker.notes)))
    for f in errors + warnings:
        print("[{}] {} {}".format("错误" if f.level == "error" else "警告", f.code, f.where()))
        print("    " + f.message)
    if not findings:
        print("结果：通过")
    else:
        print("结果：错误 {} 个，警告 {} 个".format(len(errors), len(warnings)))
    return code


if __name__ == "__main__":
    sys.exit(main())
