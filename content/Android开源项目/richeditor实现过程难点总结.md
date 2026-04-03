---
title: "RichEditor实现过程难点总结"
date: 2016-01-24 08:00:00 +0800
categories: ["Android开源项目"]
source_name: "RichEditor实现过程难点总结"
---
1.span的位置计算，期初自己写删除区间判断算法，后改为，利用inputfilter返回spanstring,利用textwatcher获得span，绑定位置
2.span的复用和变换，复用利用SPAN_EXCLUSIVE_INCLUSIVE，变换，刷新当前变成  SPAN_EXCLUSIVE_EXCLUSIVE，再插入
3.刷新时记录光标的位置，刷新完后重置光标的位置
4.回车需要拆分字符串，还需要拆分spanmodel集合，后期可以考虑优化遍历算法，改为二分法。
5.回删需要考虑合并字符串，还需要考虑合并spanmodel集合。
6.逆向保证样式和面板的统一
7.后期考虑建立对象池，防止spanmodel和span的重复创建。
8.转换markdown时算法，快排，拼接字符串。
9.选中状态监听和改变。
**嗷嗷8888** 是是 **aa**
