---
title: "一次奇葩问题导致的彻底了解View-post()的底层原理"
date: 2019-03-23 12:54:14+08:00
categories: ["Android源码分析"]
source_name: "一次奇葩问题导致的彻底了解View-post()的底层原理"
jianshu_views: 3677
jianshu_url: "https://www.jianshu.com/p/405a745aa4d0"
---
>本篇文章已授权微信公众号 stormjun94 （Android 技术人员）独家发布
### 前言
原来一直以为View.post()就是简单的利用Handler发送出去，没有什么特殊的地方，没有必要纠结具体的实现，但是最近遇到一个问题，发现一个ListView中的一个View无法点击，特别奇怪显示正常，却无法点击，我跟踪源码最后发现一直执行到了ACTION_UP，也就是说这个事件是被这个View消费了，但是最后执行`performClick()`方法的时候，居然没有回调onClick的监听回调。
```
switch (action) {
                case MotionEvent.ACTION_UP:
                    {
                    if (!focusTaken) {
                                // Use a Runnable and post this rather than calling
                                // performClick directly. This lets other visual state
                                // of the view update before click actions start.
                                if (mPerformClick == null) {
                                    mPerformClick = new PerformClick();
                                }
                                //源码执行到了这个地方，但是没有回调onClick()
                                if (!post(mPerformClick)) {
                                    performClickInternal();
                                }
                            }
                    }
 }
```
通过上面的源码，可以看到源码执行到了performClick的地方，但是最终没有回调onClick（onClickListener是存在的），这就让我不能理解了，唯一疑惑的地方就是这里，使用了post()方法，将performClick这个runnable发送了出去，所以让我纠结于是不是可以在View.post()里面研究一下。（本篇文章主要分析View.post的底层源码，关于这个问题，最后查源码，解决了，是ListView的itemView和viewType没有正确对应上的原因，但是能够正常显示，却不能点击，这里具体就不解释，后面如果有时间可以专门分析一下）
### 源码解析
View.post()不看不知道，一看才知道没有我们想象的那么容易。
```
public boolean post(Runnable action) {
        final AttachInfo attachInfo = mAttachInfo;
        if (attachInfo != null) {
            return attachInfo.mHandler.post(action);
        }

        // Postpone the runnable until we know on which thread it needs to run.
        // Assume that the runnable will be successfully placed after attach.
        getRunQueue().post(action);
        return true;
    }
```
可以看到这里，是存在两种情况的，一种attachInfo不为null的情况，一种是attachInfo为null的情况。这里就有几个问题了：
>1.attachInfo是什么？
>2.这两种情况有什么区别？
>3.第二种没有直接通过Handler发出去，怎么执行的？

我上面的问题，是最后的查明原因的关键点，就是一个在ListView正常显示的View,但是它的`attachInfo==null`。那么就来一个问题一个问题解决吧。
#### 1.AttachInfo是什么？
既然AttachInfo==null，那么我们肯定要追问，attachInfo什么时候赋值的，什么时候置空的，所以在View.java中全局搜索`mAttachInfo = `注意后面要带上一个空格，这也算一个看源码的小技巧吧，这样可以过滤很多无用的代码。
![技巧一](/assets/img/posts/7c621a89eaa447f6.png)

可以看到整个代码里面一共就两处，而且对应的正好就是一处赋值，一处置空。
```
	/**
     * @param info the {@link android.view.View.AttachInfo} to associated with
     *        this view
     */
    void dispatchAttachedToWindow(AttachInfo info, int visibility) {
        mAttachInfo = info;
        ...
    }
```
```
void dispatchDetachedFromWindow() {
        ...

        mAttachInfo = null;
        ...
        }
```
可以看到方法名也很对称，一个对应于分发绑定，一个对应于分发解绑。所以看多了源码的应该能意识到这是Google常用的一种向下分发的机制，那么我们就要找到源头。
全局搜索`dispatchAttachedToWindow`，这里直接ctrl点击是没办法查看引用，所以这里还是要利用我们IDE的另一个功能全局查找。
![技巧二](/assets/img/posts/6da7fd0f1a09200d.png)
可以看到这里除了一些特殊的像RecyclerView这种特殊组件，一眼就可以看到一个很特殊的类ViewRootImpl.java,这不就是我们所有布局的最上层布局吗，那肯定就是它了。
```
private void performTraversals() {
        host.dispatchAttachedToWindow(mAttachInfo, 0);
        }
```
这里就很清楚了，看到了我们很熟悉的一个方法，`performTraversals()`,这不就是我们页面绘制的起点吗，所以这里可以得出一条结论
>在页面绘制的起点的时候，会通过分发的方式，将顶层的mAttachInfo分发给子View。而这个mAttachInfo是在ViewRootImpl初始化的时候构造函数中new出来的。
```
public ViewRootImpl(Context context, Display display) {
        ...
        mAttachInfo = new View.AttachInfo(mWindowSession, mWindow, display, this, mHandler, this,
                context);
        ...
    }
```
可以看到，这里里面保存了很多基础信息，包括后面要使用的Handler对象。所以到这里我们第一个问题解决了。
#### 2.这两种情况有什么区别？
通过上面的分析我们知道了，一个View在绘制到页面上后，都会被attach和当前页面绑定，对应的绑定的信息里面mAttachInfo有Handler对象(主线程Handler)，还有其他对象，这也是为什么我们在自线程可以利用View.post执行UI操作的原因，因为要执行的操作会通过View内部的主线程Handler发到主线程执行。让我们再来看一下两种不同的场景。
```
public boolean post(Runnable action) {
		 //场景一
        final AttachInfo attachInfo = mAttachInfo;
        if (attachInfo != null) {
            return attachInfo.mHandler.post(action);
        }

        // Postpone the runnable until we know on which thread it needs to run.
        // Assume that the runnable will be successfully placed after attach.
        //场景二
        getRunQueue().post(action);
        return true;
    }
```
##### 场景一
如果一个正常的已经绘制到页面上的View，对应的mAttachInfo不会为null，所以当我们调用View.post的时候，会通过View内部的Handler对象，将runnable发送到主线程消息队列中执行。
#### 场景二
对于场景二可能我们会很疑惑，没有见到执行的操作， 具体的场景这里举个例子，我们都知道，在Activity的`onCreate`方法中，我们可以通过View.post()拿到我们View的宽高，这是为什么呢？其实就是这个这里的场景二有关。
首先我们知道，在`onCreate`方法中，View还没有执行页面绘制的三大操作的，这也是我们为什么不能在onCreate拿到宽高的原因，因为页面的绘制流程的起点`performTraversals()`是在Activity的`onResume`方法之后执行的，所以这时候，当我们在`onCreate`方法中，执行View.post方法，根据前面的分析，没有执行`performTraversals()`，所以没有分发attach，所以mAttachInfo为null，这时候，就会执行我们的场景二。
```
private HandlerActionQueue getRunQueue() {
        if (mRunQueue == null) {
            mRunQueue = new HandlerActionQueue();
        }
        return mRunQueue;
    }
    
    
public class HandlerActionQueue {
	//数组
    private HandlerAction[] mActions;
    private int mCount;

    public void post(Runnable action) {
        postDelayed(action, 0);
    }

    public void postDelayed(Runnable action, long delayMillis) {
        final HandlerAction handlerAction = new HandlerAction(action, delayMillis);

        synchronized (this) {
            if (mActions == null) {
                mActions = new HandlerAction[4];
            }
            //数组追加的工具类
            mActions = GrowingArrayUtils.append(mActions, mCount, handlerAction);
            mCount++;
        }
    }
}

private static class HandlerAction {
        final Runnable action;
        final long delay;

        public HandlerAction(Runnable action, long delay) {
            this.action = action;
            this.delay = delay;
        }

        public boolean matches(Runnable otherAction) {
            return otherAction == null && action == null
                    || action != null && action.equals(otherAction);
        }
    }
```
我们这里可以看到，其实很简单，就是将我们要执行的runnable利用一个数组保存了起来，也就是说当我们在onCreate中执行View.post的时候，并没有立即执行我们要执行的方法，而是被保存了起来。那么这里场景二和场景一的区别其实也是很明显了，那么就到了最后一个问题。
##### 3.第二种没有直接通过Handler发出去，怎么执行的？
通过上面我们知道，我们没执行的Runnable被保存了起来，在上面提到的HandlerActionQueue类中，我们找寻相关的方法，可以看到，一个关键方法（其实类很短，很好找，而且方法名也很直接）
```
public void executeActions(Handler handler) {
        synchronized (this) {
            final HandlerAction[] actions = mActions;
            for (int i = 0, count = mCount; i < count; i++) {
                final HandlerAction handlerAction = actions[i];
                handler.postDelayed(handlerAction.action, handlerAction.delay);
            }

            mActions = null;
            mCount = 0;
        }
    }
```
可以看到这里有个很明显的执行的方法，通过传入的Handler对象，遍历保存的数组，然后再将保存的runnable再通过handler发出去，传入到Handler对应的消息队列中。
这次先按住ctrl，看一下使用的类，发现有调用，一共有两处，一处和ViewRootIml有关一处和View有关。
![技巧三](/assets/img/posts/abfc219874d211e0.png)
起初我没有多想，直接去看ViewRootIml的源码直接以为在这里就处理了，后来感谢@[神天圣地](https://www.jianshu.com/u/d46a1b0c9492)的提醒，这里应该是在View的`dispatchAttachedToWindow`分发的时候，才处理的，因为HandlerActionQueue对象是不一样的。
```
private void performTraversals() {
...
// Execute enqueued actions on every traversal in case a detached view enqueued an action
        getRunQueue().executeActions(mAttachInfo.mHandler);
        ...
        //执行绘制三大步骤
}
```
```
void dispatchAttachedToWindow(AttachInfo info, int visibility) {
  // Transfer all pending runnables.
        if (mRunQueue != null) {
            mRunQueue.executeActions(info.mHandler);
            mRunQueue = null;
        }
}
```
可以看到，这里又一次将`mAttachInfo`中的Handler传入，然后便会把我们通过View.post保存的runnable再发送到主线程的消息队列中，等待执行，由于后面里面会执行第一次到绘制步骤，所有，当执行到我们的runnable的时候，肯定就可以拿到View的宽高了。
### 特别注意
##### 通过View.post拿到的宽高一定是真实的吗？
这个不一定，上面也提到了，这里只是第一次绘制的步骤，如果像RelativeLayout，或者其他特殊的View，再某些特殊情况下，会执行多次绘制，如果我们的runnable在第一次绘制结束后就里面执行，那么就拿到的只是第一次绘制结束后的宽高。当然，绝大部分拿到的是真实的宽高。
##### View的attach和detach一定只有ViewRootImpl执行吗？
不一定，例如一些特殊的存在组件复用的RecyclerView，都存在自己定制的attach和detach操作，具体可以看我写的关于[RecyclerView的系列博客](https://www.jianshu.com/p/c52b947fe064)，可以让你深层次的了解RecyclerView。

### 总结
通过这次的分析，看似简单的View.post的分析过程其实涉及到了Handler机制，View的绘制流程等很多重要的知识点，现在看来还是很值得我们阅读这个的源码的。

### 相关博客推荐
1.[【Android源码解析】View.post()到底干了啥 - 请叫我大苏 - 博客园](https://www.cnblogs.com/dasusu/p/8047172.html)
2. [通过View.post()获取View的宽高引发的两个问题：1post的Runnable何时被执行，2为何View需要layout两次；以及发现Android的一个小bug](https://blog.csdn.net/scnuxisan225/article/details/49815269)
