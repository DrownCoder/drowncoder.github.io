---
title: java中list集合的clear
date: 2017-09-26 00:27:11+08:00
categories: ["Android基础"]
source_name: "java中list集合的clear"
jianshu_views: 1528
jianshu_url: "https://www.jianshu.com/p/16d3c08e981d"
---
java中list集合通过clear()方法清空，只会将list中的对象变成垃圾回收清空，但是list对象还是存在。
但是通过list=null后，不仅列表中的对象变成了垃圾,为列表分配的空间也会回收,什么都不做与赋值NULL一样,说明直到程序结束也用不上列表list了,它自然就成为垃圾了.clear()只是清除了对象的引用,使那些对象成为垃圾.
来自于博客:http://li348720255.blog.163.com/blog/static/7671319320118210515459/
