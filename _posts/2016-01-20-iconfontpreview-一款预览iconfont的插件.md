---
title: "背景"
date: 2019-02-25 23:38:21+08:00
categories: ["Android开源项目"]
source_name: "IconFontPreview——一款预览IconFont的插件"
jianshu_views: 4419
jianshu_url: "https://www.jianshu.com/p/369a7b251729"
---
使用过IconFont的应该都深有体会，每次使用IconFont的时候，由于不知道Unicode和Icon的对应关系，每次都要到对应的文件夹下找到默认生成的html文件，打开后才能寻找到我们需要的IconFont。而每次找文件这个过程真的很麻烦，而且当公司IconFont的版本更新的时候，这个路径也会相应改变，那就更痛苦了。
为了解决这个问题，我就考虑能不能做一款预览IconFont的插件，避免这种痛苦的寻找文件过程，提高开发效率。
### 功能特性
* 支持已定义的IconFont的预览
* 支持缓存避免每次查找
* 使用方便
### 源码地址
[IconFontPreview](https://github.com/DrownCoder/IconFontPreview)
>欢迎Star👏～
>欢迎提issue和PR～
这里再推荐一下我的另一个开源项目[EasyTextView](https://github.com/DrownCoder/EasyTextView)，一款高效利用IconFont的TextView，功能丰富，用过的人都说好～
### jar包地址
>我已经发布到Intellij的官网上了，不知道为啥搜不到

[IconFontPreview.zip](https://github.com/DrownCoder/IconFontPreview/blob/master/IconFontPreview.zip)
### 使用步骤
##### 1.安装完插件后,在操作面板会生成一个草帽的Icon，点击操作面版的草帽icon(ONE PIECE)
![step1](https://upload-images.jianshu.io/upload_images/7866586-94afdf6f1cc117ae.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
##### 2.第一次需要设置工程下ttf字体文件路径和定义iconfont的string.xml路径
![step2.jpg](https://upload-images.jianshu.io/upload_images/7866586-0ba179c2588835f6.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

这一步只会在第一次才会使用，因为本地会有缓存，后面的会读取缓存的目录（根目录下的PlugCache）
##### 3.点击确定后或者以后在点击草帽就会在浏览器中打开预览定义的IconFont图标了
![ONE PIECE](https://upload-images.jianshu.io/upload_images/7866586-b58b9e8dd4578db1.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
##### 4.后面再使用就可以直接点击操作面板的草帽Icon就会直接弹出预览页面了
### 实现原理
#### 1.IntelliJ插件开发
这个网上博客很多，这里就不专门讲解了
#### 2.XML解析
>这里本来一开始是准备直接读取ttf文件，然后直接生成ttf文件中所有定义的IconFont的，但是我好像没有找到实现方式（大家有好的实现方式可以告诉我～，或者提PR）
我们一般定义IconFont的都会在String.xml定义unicode类似于下面
```
<resources>
    <!--后退-->
    <string name="icon_font_606">\ue606</string>
    <!--评论-->
    <string name="icon_font_comment">\ue68f</string>
    <!--收藏-->
    <string name="icon_font_collection">\ue68e</string>
    <!--赞-->
    <string name="icon_font_like">\ue695</string>
</resources>
```
所以这里就需要我们遍历XML了，这里我选择了SAX解析的方式，取出了定义的Key，和对应的Unicode，并保存起来
#### 3.Jsoup动态渲染HTML
拿到我们的数据集后，我们就需要生成我们最终的预览页面了，这里直接利用IconFont固定的HTMl模版，下载下来，利用Jsoup这个HTMl解析库，遍历我们生成的数据集，并对应在固定位置插入HTML代码，最后利用File保存到PluginCache文件夹下
这里有几个问题：
##### 3.1 jar包中HTML读取css文件路径问题
由于插件最终生成的是jar文件，所有html中的css文件，由于路径无法读取，需要将css文件拷贝到html中
##### 3.2 缓存文件需要利用文件流保存，这里涉及到插件的数据持久化。
因为用户设置的ttf文件路径和string.xml文件路径不能每次点击都要重新设置，哪还要这个插件干啥...，所以我就想将用户设置的这两个路径缓存起来，所以这里就涉及到插件的数据持久化。
网上提供的插件持久化的两种方式我都试了一下，发现没法真正意义上的持久化，当你idea关闭后，这些数据都会被对应清理掉，对应于
1.使用PersistentStateComponent
2.使用PersistentStateComponent
所以最后我是用了文件流的方式缓存目录路径（大家如果有更好的方式可以告诉我～）
```
/**
     * 创建li
     */
public static final String ICON_ITEM = "<li>\n" +
            "                <i class=\"icon iconfont\">%s</i>\n" +
            "                    <div class=\"name\">%s</div>\n" +
            "                    <div class=\"code\">%s</div>\n" +
            "                </li>";
public void printer(String ttfPath) {
        InputStream html = this.getClass().getResourceAsStream(Common.HTML_PATH);
        try {
            Document doc = Jsoup.parse(html, "UTF-8", "");
            if (data != null) {
                Elements style = doc.select("style");
                style.prepend(String.format(Common.STYLE_DF, ttfPath));
                Elements container = doc.getElementsByClass("icon_lists clear");
                if (Common.MODE_ALL) {
                    //全量模式，从16进制最小值到16进制最大值
                    printerAll(container);
                } else {
                    //自定义模式,只输出定义的资源文件
                    printerDefine(container);
                }
            }
            File result = CreateFileUtil.createFile(RESULT_PATH);
            if (result == null) {
                return;
            }
            FileOutputStream outStream = new FileOutputStream(result);    //文件输出流用于将数据写入文件
            outStream.write(doc.toString().getBytes(StandardCharsets.UTF_8));
            outStream.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void printerDefine(Elements container) {
        for (Map.Entry<String, XmlIconFontModel> entry : data.getFonts().entrySet()) {
            String code = entry.getValue().getFontValue();
            if (code.startsWith(Common.ICON_START)) {
                String value = "&#xe" + code.substring(3) + ";";
                container.append(String.format(Common.ICON_ITEM, value,
                        entry.getValue().getFontKey(), code));
            } else if (code.startsWith(Common.ICON_START_SUB)) {
                container.append(String.format(Common.ICON_ITEM, code,
                        entry.getValue().getFontKey(), code));
            }
        }
    }
```

#### 4.利用exec执行命令，打开生成的html文件

```
/**
         * 执行展示
         */
        try {
            if (OSinfo.isWindows()) {
                Runtime.getRuntime().exec("cmd.exe /c start " + RESULT_PATH);
            } else {
                Runtime.getRuntime().exec("open " + RESULT_PATH);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
```

### 相关推荐
[【干货】基于iconfont拓展的EasyTextView(高度自定义，丰富Api，支持左右设置Text,设置Shape,设置span等)](https://www.jianshu.com/p/7669557b9181)

[EMvp-基于AOP的一种RecyclerView多楼层开发模式，支持组件化，全局楼层打通，MVP等高拓展性功能](https://www.jianshu.com/p/f45e4bcb8d92)