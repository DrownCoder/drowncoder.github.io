---
title: "《Android开发艺术探索》读书笔记-第二章 IPC机制（未啃透）"
date: 2017-09-26 00:26:01+08:00
categories: ["读书笔记"]
source_name: "《Android开发艺术探索》读书笔记-第二章-IPC机制（未啃透）"
jianshu_views: 247
jianshu_url: "https://www.jianshu.com/p/5b798a779133"
---
## 2.2 Android中的多进程模式
### 2.2.1 开启多进程模式
1)开启多进程方式：在AndroidMenifest.xml文件中为四大组件指定android:process属性
2)“：”和完整进程名的区别：“：”的含义是指要在当前的进程名前附加上当前的包名，而完整进程名就是以完整的名字为命名，不会附加信息；以“：”开头的进程属于当前应用的私有进程，其他应用的组件不可以和它跑在同一个进程中，而进程名不以“：”开头的进程属于全局进程，其他应用通过ShareUID方式可以和它跑在同一个进程中以实现共享数据。
### 2.2.2 多进程模式的运行机制
1)每个进程会有一个单独的虚拟机，在内存分配上有不同的地址空间。
2)多进程会造成的问题：
(1)静态成员和单例模式完全失效:不同的进程有单独的虚拟机，单独的地址空间，对应的对象也不同，有副本。
(2)线程同步机制完全失效：内存不同，锁的对象也不同。
(3)SharePreferences的可靠性下降：SharePreferences底层是通过读/写XML实现的，但是同样会产生并发性问题。
(4)Application会多次创建：单独创建了虚拟机相当于启动了一次应用，所以就会启动Application。
## 2.3 IPC基础概念介绍
### 2.3.1 Serializable接口
1)java提供的序列化接口
2)对于serialVersionUID，用于在反序列化时和对象中的serialVersionUID比较，相同则可以序列化成功，不指定也可以，建议指定。
### 2.3.2 Parcelable接口
1)Android平台上的序列化方式，效率比Serializable高，推荐在Android平台上使用，因为Serializable需要大量的I/O流进行序列化和反序列化操作，但是Parcelable使用较麻烦。
2)序列化功能是通过writeToParcel方法实现的，反序列化是通过CREATOR实现的。**这里需要写个Demo**。
### 2.3.3 Binder
**这一章需要以后再看一遍**
## 2.4 Android中的IPC方式
### 2.4.1 使用Bundle
四大组件中的三大组件都支持在Intent中传递Bundle数据，由于Bundle实现了Parcelable接口所以它可以方便地在不同的进程间传输。
### 2.4.2 使用文件共享
共享文件可以实现进程间通信，两个进程通过读/写同一个文件来交换数据，由于Android基于Linux系统，使得其并发读/写文件可以没有限制地进行。所以要避免并发写这种情况的法身，可能会导致问题。所以文件共享适用于对于数据同步要求不高的进程间通信。

特例：Sharedpreferences是Android提供的轻量级存储方案，使用过键值对存储数据的，底层是采用XML来存储键值对。Sharedpreferences的存储目录在/data/data/package name/shared_prefs目录下。虽然SharedPreferences属于文件一种，但是由于系统对于它的读写有一定的缓存策略，即在内存中会有一份Sharedpreferences文件的缓存，所以不建议在进程间通信中使用Sharedpreferences。
### 2.4.3 使用Messenger
Messenger是一种轻量级的IPC方案，底层使用AIDL实现的。通过Messenger在不同进程间传递Message对象，在Message中放入我们需要传递的数据，从而完成数据在进程间的传递。
缺点：
1.只能用来传递数据，不适合用于调用服务端的方法。
2.只能以串行的方式处理客户端发来的消息，服务端不能处理大量的并发的请求。
**这里需要写个Demo**
### 2.4.4 使用AIDL