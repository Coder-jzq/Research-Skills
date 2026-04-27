# Research-Skills
科研过程中的skills：读论文、复现代码、初稿撰写启发...


<hr/>

## 以(anan-paper-reader)skill使用方法为例

这是一个用于 Codex 的论文阅读 Skill。安装后，你可以把一篇论文 PDF 提供给 Codex，让 Codex 使用该 Skill 生成结构化的中文论文精读总结。

---

## 1. 安装 Skill

首先，克隆本项目：

```
下载 codec/paper_reading/anan-paper-reader
```

创建 Codex 的 skills 目录：

```bash
mkdir -p ~/.agents/skills
```

将整个 `anan-paper-reader` 文件夹复制到 Codex 的 skills 目录中：

```bash
cp -r anan-paper-reader ~/.agents/skills/
```

安装完成后，目录结构应类似如下：

```text
~/.agents/skills/
└── anan-paper-reader/
    ├── agents/
    ├── references/
    ├── scripts/
    └── SKILL.md
```

注意：请复制整个 `anan-paper-reader` 文件夹，不要只复制 `SKILL.md`。

最后，在codex 使用skill读论文就好啦。


输出例子：
<img width="765" height="964" alt="image" src="https://github.com/user-attachments/assets/816d18e6-e6f4-4780-9eb2-9c933e928b22" />
<img width="1027" height="960" alt="image" src="https://github.com/user-attachments/assets/17385cb0-1d58-4f78-b0c0-971b7e2b76d9" />
<img width="808" height="690" alt="image" src="https://github.com/user-attachments/assets/32b499c0-fb8f-4bb7-9032-ccea985ebcad" />


