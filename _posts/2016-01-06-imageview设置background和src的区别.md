---
title: ImageView设置background和src的区别
date: 2017-09-26 00:27:38+08:00
categories: ["Android基础"]
source_name: "ImageView设置background和src的区别"
jianshu_views: 9170
jianshu_url: "https://www.jianshu.com/p/3851e4d34fff"
---
今天开发的时候遇到一个小问题，在给一个ImageView更换图片的时候，我使用的是java的方式更换，使用的方法是setBackgroundResource（）,但奇怪的是总是没有效果。
最后查明原因是：我在编写xml文件的时候，为了查看效果，给这个ImageView设置了src，这时候再设置background的时候回发生重叠。
解决方法：将xml中的src删除即可。

问题延伸：
**一、ImageView设置background和src的区别。**
1.src是图片内容（前景），bg是背景，可以同时使用。
2.background会根据ImageView组件给定的长宽进行拉伸，而src就存放的是原图的大小，不会进行拉伸 。
3.scaleType只对src起作用；bg可设置透明度。

**二、ImageView几种不同的设置图片的方式。**
设置background：
1.image.setBackground(getResources().getDrawable(R.drawable.blackk));//变形
2.image.setBackgroundResource(R.drawable.blackk);//变形       3.image.setBackgroundDrawable(getResources().getDrawable(R.drawable.blackk));////变形
**源码：这三种方法的实质都是调用方法3setBackgroundDrawable()。**
 
 设置src:
1.image.setImageDrawable(getResources().getDrawable(R.drawable.blackk)); //不会变形
2.Stringpath=Environment.getExternalStorageDirectory()+File.separator+"test1.jpg";
 Bitmap bm = BitmapFactory.decodeFile(path); 
 image.setImageBitmap(bm);//不会变形
 3.image.setImageResource(R.drawable.blackk);//不会变形
**源码： 其中方法2就是将bitmap转换为drawable然后调用方法1，方法1和方法3都是调用updateDrawable（）方法。**

