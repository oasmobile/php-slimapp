"""通过已登录的 gh/glab 调用同仓 PR/MR API。"""
import json
import re
import subprocess
from urllib.parse import quote, urlencode, urlsplit

from mdf_core.foundation.errors import MDFError
from mdf_core.workspace.merge_policy import git


def origin(repo, provider):
    raw = git(repo, "remote", "get-url", "origin").stdout.strip()
    push = git(repo, "remote", "get-url", "--push", "--all", "origin").stdout.splitlines()
    if push != [raw]:
        raise MDFError("origin 的 fetch/push 地址必须一致且唯一", code="ambiguous_origin")
    if "://" in raw:
        parsed = urlsplit(raw)
        host = parsed.hostname if parsed.scheme == "ssh" else parsed.netloc.rsplit("@", 1)[-1]
        project = parsed.path.strip("/")
    else:
        match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", raw)
        if not match:
            raise MDFError("PR mode 需要 SSH 或 HTTPS origin", code="invalid_origin")
        host, project = match.groups()
    project = project.removesuffix(".git")
    if (not host or not project or any(p in {"", ".", ".."} for p in project.split("/"))
            or (provider == "github" and len(project.split("/")) != 2)):
        raise MDFError("无法解析 origin 项目", code="invalid_origin")
    return {"provider": provider, "host": host, "project": project, "origin": raw}


class Forge:
    def __init__(self, repo, identity):
        self.repo, self.identity = repo, identity
        self.github = identity["provider"] == "github"
        project = identity["project"]
        self.endpoint = f"repos/{project}/pulls" if self.github else f"projects/{quote(project, safe='')}/merge_requests"

    def api(self, endpoint, method="GET", body=None):
        command = ["gh" if self.github else "glab", "api", "--hostname", self.identity["host"],
                   "--method", method, endpoint]
        if body is not None:
            command += ["--input", "-"]
        try:
            result = subprocess.run(command, cwd=self.repo, input=json.dumps(body) if body is not None else None,
                                    text=True, capture_output=True, check=False)
        except OSError as exc:
            raise MDFError("请安装并登录 gh/glab", code="forge_unavailable") from exc
        if result.returncode:
            raise MDFError(result.stderr.strip() or "平台 API 失败", code="forge_failed")
        try:
            return json.loads(result.stdout)
        except ValueError as exc:
            raise MDFError("平台未返回 JSON", code="forge_invalid_response") from exc

    def normalize(self, raw):
        if self.github:
            project = self.identity["project"].casefold()
            same = str((raw.get("head", {}).get("repo") or {}).get("full_name", "")).casefold() == project
            same = same and str((raw.get("base", {}).get("repo") or {}).get("full_name", "")).casefold() == project
            result = {"id": raw["number"], "url": raw["html_url"], "source": raw["head"]["ref"],
                      "target": raw["base"]["ref"], "head": raw["head"]["sha"],
                      "state": "merged" if raw.get("merged_at") or raw.get("merged") else raw["state"],
                      "merge_commit": raw.get("merge_commit_sha")}
        else:
            same = raw.get("source_project_id") == raw.get("target_project_id") and raw.get("source_project_id") is not None
            result = {"id": raw["iid"], "url": raw["web_url"], "source": raw["source_branch"],
                      "target": raw["target_branch"], "head": raw["sha"],
                      "state": "open" if raw["state"] == "opened" else raw["state"],
                      "merge_commit": raw.get("merge_commit_sha")}
        if not same:
            raise MDFError("只支持 origin 同仓 PR/MR", code="foreign_pull_request")
        return result

    def get(self, number):
        return self.normalize(self.api(f"{self.endpoint}/{int(number)}"))

    def find(self, source, target):
        query = ({"state": "all", "head": self.identity["project"].split("/")[0] + ":" + source, "base": target}
                 if self.github else {"state": "all", "source_branch": source, "target_branch": target, "scope": "all"})
        found = []
        page = 1
        while True:
            rows = self.api(self.endpoint + "?" + urlencode({**query, "per_page": 100, "page": page}))
            if not isinstance(rows, list):
                raise MDFError("PR/MR 列表无效", code="forge_invalid_response")
            for row in rows:
                item = self.normalize(row)
                if item["source"] == source and item["target"] == target:
                    found.append(item)
            if len(rows) < 100:
                break
            page += 1
        if len(found) > 1:
            raise MDFError("同一来源和目标有多个 PR/MR，不能自动选择", code="ambiguous_pull_request")
        return self.get(found[0]["id"]) if found else None

    def create(self, source, target, title, description):
        body = ({"head": source, "base": target, "title": title, "body": description} if self.github else
                {"source_branch": source, "target_branch": target, "title": title, "description": description,
                 "remove_source_branch": False, "squash": False})
        return self.normalize(self.api(self.endpoint, "POST", body))
