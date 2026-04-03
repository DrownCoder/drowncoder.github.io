---
title: "EMvp遇到的问题"
date: 2016-01-19 08:00:00 +0800
categories: ["Android开源项目"]
source_name: "EMvp遇到的问题"
---
1.注解处理器的处理
2.注解处理器注解，错误检测
3.注解获取class类型需要try-catch
4.不是全局的组件
2.mvc到mvp到vimip
3.ComponentRule的组件化和R变量的组件化
4.Presenter的组件化
5.view默认presenter，一个Activity存在多个Presenter，Presenter注入
6.Presenter拦截
7.匿名内部类和静态内部类的构造函数的反射

1.三种组件模式
a.组件依赖页面，组件只展示UI，组件本身没有生命周期，组件的事件交给页面处理，然后刷新数据
b.组件自身维护一套体系，自身内部逻辑闭合，只依赖于model，组件需要感知生命周期，处理生命周期相关的操作。依赖于ViewHolder携带。
c.在b的基础上，组件内部需要对修改关闭，对拓展开放，组件自身实现细粒度的MVP。依赖于Model携带，不仅仅ViewHolder需要感知生命周期，model也需要感知生命周期。
