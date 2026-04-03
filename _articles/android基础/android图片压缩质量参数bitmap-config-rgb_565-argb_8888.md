---
title: "android图片压缩质量参数Bitmap-Config-RGB_565-ARGB_8888"
category: "Android基础"
category_slug: "android基础"
source_name: "android图片压缩质量参数Bitmap-Config-RGB_565-ARGB_8888"
sort_key: 0009
---
android中的大图片一般都要经过压缩才显示，不然容易发生oom，一般我们压缩的时候都只关注其尺寸方面的大小，其实除了尺寸之外，影响一个图片占用空间的还有其色彩细节。

打开Android.graphics.Bitmap类里有一个内部类Bitmap.Config类，在Bitmap类里createBitmap(intwidth, int height, Bitmap.Config config)方法里会用到，打开个这个类一看

枚举变量
public static final Bitmap.Config ALPHA_8
public static final Bitmap.Config ARGB_4444
public static final Bitmap.Config ARGB_8888
public static final Bitmap.Config RGB_565

一看，有点蒙了，ALPHA_8, ARGB_4444,ARGB_8888,RGB_565 到底是什么呢？

其实这都是色彩的存储方法：我们知道ARGB指的是一种色彩模式，里面A代表Alpha，R表示red，G表示green，B表示blue，其实所有的可见色都是右红绿蓝组成的，所以红绿蓝又称为三原色，每个原色都存储着所表示颜色的信息值

说白了就ALPHA_8就是Alpha由8位组成
ARGB_4444就是由4个4位组成即16位，
ARGB_8888就是由4个8位组成即32位，
RGB_565就是R为5位，G为6位，B为5位共16位

由此可见：
ALPHA_8 代表8位Alpha位图
ARGB_4444 代表16位ARGB位图
ARGB_8888 代表32位ARGB位图
RGB_565 代表8位RGB位图

位图位数越高代表其可以存储的颜色信息越多，当然图像也就越逼真。

用法：

在压缩之前将option的值设置一下：

options.inPreferredConfig = Bitmap.Config.RGB_565
