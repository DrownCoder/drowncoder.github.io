# GitHub 博客迁移项目

这个目录已经整理成一个可部署到 GitHub Pages 的 Jekyll 博客。

## 目录说明

- `content/`：唯一需要维护的文章目录
- `_layouts/`：页面模板
- `assets/css/style.css`：站点样式
- `user-7866586-1775056047/`：解压后的原始文章备份
- `user-7866586-1775056048.rar`：原始压缩包

## 发布到 GitHub Pages

1. 在 GitHub 新建仓库。
2. 把当前目录内容推送到仓库。
3. 打开 GitHub 仓库的 `Settings -> Pages`。
4. 在 `Build and deployment` 中选择 `Deploy from a branch`。
5. 分支选择 `main`，目录选择 `/ (root)`。
6. 如果仓库名不是 `<你的用户名>.github.io`，先打开 `_config.yml`，把 `baseurl` 改成 `/<仓库名>`。
7. 保存后等待 GitHub 自动构建。

如果仓库名是 `<你的用户名>.github.io`，博客地址会是：

`https://<你的用户名>.github.io/`

如果仓库名是普通项目名，比如 `blog`，地址通常会是：

`https://<你的用户名>.github.io/blog/`

这时 `_config.yml` 里的配置应当类似：

```yml
url: "https://<你的用户名>.github.io"
baseurl: "/blog"
```

## 本地预览

当前站点已切换为 `Chirpy`。这个主题在线上推荐通过 GitHub Actions 构建，本机如果使用较老的 Ruby / Jekyll 版本，可能无法完整预览最新主题效果。

如果你的本机环境较新，仍然可以尝试：

```bash
cd /Users/xuan/Projects/Blogs
bundle install --path vendor/bundle
bundle exec jekyll serve
```

启动后访问：

`http://127.0.0.1:4000/`

如果仓库有权限或依赖版本提示，可以优先使用：

```bash
bundle config set path 'vendor/bundle'
bundle install
bundle exec jekyll serve
```

## Chirpy 说明

- 站点已改为 `Chirpy` 风格，并把旧文章迁移到 `_posts/`
- GitHub Actions 工作流位于 `.github/workflows/pages-deploy.yml`
- 如果 GitHub Pages 未自动发布，请到仓库 `Settings -> Pages` 中确认 `Source` 使用 `GitHub Actions`

## 内容目录

现在博客内容统一收口到 `content/`。

你以后只需要维护这一个目录：

- 老文章：直接在 `content/` 里改
- 新文章：也直接放到 `content/` 里

### 新文章怎么写

最简单的方式就是直接新建一个 Markdown 文件：

```md
# 我的新文章

这里直接开始写正文。
```

你不需要自己处理：

- Jekyll 文件名
- front matter
- 发布时间

GitHub Actions 构建时会自动把 `content/` 里的 Markdown 转成真正发布用的 `_posts/`。

### 分类怎么控制

- 直接放在 `content/` 根目录：默认分类是 `未分类`
- 放到子目录：子目录名会自动变成分类

例如：

- `content/Android/Jetpack笔记.md` -> 分类 `Android`
- `content/读书/Gradle/学习记录.md` -> 分类 `读书 / Gradle`

现在仓库里的老文章也已经按目录收好了，例如：

- `content/Android源码分析/`
- `content/Android基础/`
- `content/Android开源项目/`
- `content/读书笔记/`
- `content/旅游/`

如果你调整了文章所在文件夹，构建时会自动把新的文件夹路径同步成文章分类。

### 老文章怎么编辑

老文章已经在 `content/` 里，直接改对应的 Markdown 即可。  
提交并推送后，线上会自动重新发布。

### 发布命令

```bash
git add .
git commit -m "Update posts"
git push origin master
```
