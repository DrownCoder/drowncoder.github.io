---
title: "Retrofit源码分析（一）-基本流程"
category: "Android源码分析"
category_slug: "android源码分析"
source_name: "Retrofit源码分析（一）-基本流程"
sort_key: 0034
---
Retrofit源码分析（一）-基本流程
### 前言
>前面几篇博客分析了从流程和过滤器两个角度分析了OkHttp，对OkHttp算是有了一个初步的理解，具体有兴趣的可以去看一下[okhttp源码分析系列](http://www.baidu.com "okhttp源码分析系列")。借着okhttp的热度，顺手将retrofit的源码看了一下，接下来也就对retrofit的源码进行一下分析。

其实一开始看retrofit我是抱着几个问题来看的：

1. 什么是RESTful
2. retrofit的执行流程是怎样的，对OkHttp的流程有没有什么改变
3. retrofit的显著特点是什么
4. retrofit到底好在哪里
5. retrofit的艺术设计
6. retrofit的适用场景

为什么会有这些问题哪，因为其实看完Volley源码和okHttp源码后会发现，其实就网络通信优化而言现有的无论是使用原生网络还是OkHttp加上一些列缓存，Okio等网络优化，已经优化的比较成功了。而用过retrofit，肯定都对retrofit有一定的了解，retrofit其实底层就是使用OkHttp，也就是在OkHttp的基础上进行再一次的封装，但是却里面受到热捧，而且使用过retrofit原生的构建网络请求的流程都会发现，使用起来并不是特别容易，如果到项目级别的开发，肯定要基于retrofit再进行一次封装，这样到头来封装了多次。综上所述，不免让我有以上一些问题，也让我对retrofit的源码产生了兴趣，抱着问题来看源码也更便于理解一个网络框架的设计思想。
接下里的分析其实也就是围绕上面的问题展开的。
### 什么是RESTful
其实基本上搞IT的应该都听过RESTful这个词吧，retrofit为什么好的也是因为它很适合RESTful这种形式的接口类型，那么问题来了，**到底何为RESTful？？？**这其实一直是一个很困扰我的问题，起初我对他的概念只是一种接口的定义规范，但是强迫症的我总想**深刻**的理解学习一下，各种搜索之后，发现了几个不错的科普帖子供大家学习：
>[怎样用通俗的语言解释REST，以及RESTful？](https://www.zhihu.com/question/28557115 "怎样用通俗的语言解释REST，以及RESTful？") （知乎）  
>[Retrofit解析1之前哨站——理解RESTful](http://www.jianshu.com/p/52f3ca09e2ed "Retrofit解析1之前哨站——理解RESTful")(简书)

以上两篇帖子阅读完后，如果让我向大家用语言描述RESTful，我认为还是很难的，但至少对RESTful不只是停留在最开始的理解了，从上面两篇帖子上其实我认为最让我好理解的有这两句话，在这里放出来供大家参考：
>1.就是用URL定位资源，用HTTP描述操作。  
>2.URL定位资源，用HTTP动词（GET,POST,DELETE,DETC）描述操作。

这两句话其实意思还是比较相近的，从上面两句话其实可以很通俗的在一定程度上对RESTful有了一定的理解，这也为我们后面看retrofit的源码打下一定的基础。
### 基本流程
这里为什么先分析基本流程其实也是有原因的，想要探究一个框架的优劣肯定首先要从代码流程上理解这个框架，其次再从设计思想上学习这个框架，最后才能对这个框架有一个理性的分析。
