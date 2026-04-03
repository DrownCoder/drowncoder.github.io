* 查看分支从哪个分支拉出来的？
 `git reflog show <branch name>`
* 更新分支
`git fetch`
* 查看远程分支与本地分支映射关系:
`git branch -vv`
* 创建新的远端分支
`git checkout -b my-test  //在当前分支下创建my-test的本地分支分支`
`git push origin my-test  //将my-test分支推送到远程`
`git branch --set-upstream-to=origin/my-test //将本地分支my-test关联到远程分支my-test上   `

* adb命令合集
* 过滤errror的logcat
`adb logcat '*:E'|grep 'tag'`
