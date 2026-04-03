---
title: "第三章 View的事件体系"
date: 2017-09-26 00:26:13+08:00
categories: ["读书笔记"]
source_name: "《Android开发艺术探索》读书笔记-第三章-View的事件体系"
jianshu_views: 270
jianshu_url: "https://www.jianshu.com/p/734d48fdcd26"
---
##3.1 View的基础知识
###3.1.2 View的位置参数
1）View的位置参数top,left,right,bottom都是View相对于父容器的位置坐标  
2）x = left + translationX；y = top + translationY  
3)View在平移的过程中top和left并不会发生改变，改变的是translationX、translationY、x、y
###3.1.3 MotionEvent和TouchSlop
1)getX/getY返回的是相对于当前View左上角的x和y的坐标，而getRawX/getRawY返回的是相对于手机屏幕左上角的x和y坐标。  
2)TouchSlop是系统能识别出的被认为是滑动的最小距离。通过ViewConfiguration.get(getContext()).getScaledTouchSlop()来获取这个常量，根据这个常量可以用来过滤用户的小距离滑动。  
### 3.1.4 VelocityTracker、GestureDetector和Scroll 
VelocityTracker用来监测用户的手指滑动速度。GestureDetector用来监测用户的手势。Scroller用来滑动View对象。
## 3.2 View的滑动
### 3.2.1 使用scrollTo/scrollBy
1)scrollTo（x,y）是绝对滑动,即滑动到x，y的坐标处，scrollBy（x,y）是相对滑动，即滑动到相对原来位置的x，y坐标处。  
2)scrollTo和scrollBy只能改变View的内容的位置而不能改变View在布局中的位置
3）从左向右滑动，mScrollX为负值，反之为正值；从上往下滑动，mScollY为负值，反之为正值。
### 3.2.2使用动画
1)View动画在动画结束后，并不是真的改变位置参数,不能触发点击事件，但是属性动画可以。
2)在Android3.0以下的手机上通过nineoldandroids来实现的属性动画本质上仍然是View动画。
### 3.2.3使用布局参数
可以通过更改LayoutParams的方式去实现View的滑动。
## 3.3弹性滑动
使用Scroller，动画，handler实现延时滑动。
## 3.4View的事件分发机制
### 3.4.1 点击事件的传递规则
1)ViewGroup处理事件的流程：对于一个根ViewGroup来说，点击事件产生后，首先会传递给它，ViewGroup的dispathTouchEvent方法就会被调用，如果这个ViewGroup的onInterceptTouchEvent方法返回true就表示它要拦截当前事件，接着事件就交给这个ViewGroup处理，即它的onTouchEvent方法就会被调用；如果这个ViewGroup的onInterceptTouchEvent方法返回false就表示它不会拦截当前事件，这时当前事件就会继续传递给它的子元素，接着子元素的dispathTouchEvent方法就会被调用，子元素继续走相同的处理流程。
2)View处理事件的流程：判断是否有OnTouchListener，如果有，则OnTouchListener的onTouch方法就会被回调，这时事件处理结果还要看onTouch的返回值，如果返回false，则当前View的onTouchEvent将会被调用；如果true，则onTouchEvent不会被调用。在onTouchEvent中，如果设置的有OnTouchListener，则onClick方法会被调用。
### 3.4.2 事件分发的源码解析
1)首先事件开始会交给Activity所属的Window进行分发。Window对应的实现类是PhoneWindow,PhoneWindow会将事件直接传递给DecorView。
2)子元素能够接受点击事件主要由两点来衡量:**子元素是否在播放动画**和点击事件的坐标是否落在子元素的区域内。
## 3.5 View的滑动冲突
### 3.5.1 常见的滑动冲突场景
1)外部的滑动方向和内部滑动方向不一致。
2)外部的滑动方向和内部的滑动方向一致。
3)多种滑动情况嵌套。
### 3.5.2 滑动冲突处理规则
需要外部处理则外部拦截事件，需要内部处理则内部阻挡外部拦截。
### 3.5.3 滑动冲突的解决方式
1)外部拦截法，重写父容器的onInterceptTouchEvent方法，在ACTION_MOVE事件时根据相应情形判断该由谁处理，对应进行相应的拦截。
2)内部拦截法，重写子元素的dispathTouchEvent方法，利用requestDisallowInterceptTouchEvent（boolean）方法，当为true，表示子元素要求父元素不能拦截这个事件。对应父元素需要拦截除ACTION_DOWN以外的其他事件，这样当子元素调用requestDisallowInterceptTouchEvent（false）方法时，父元素才能继续拦截所需的事件。**为什么父元素不拦截ACTION_DOWN事件呢？因为源码中ACTION_DOWN事件并不受FLAG_DISALLOW_INTERCEPT标志位控制**
