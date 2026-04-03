---
title: 【重拾Handler】——postDelayed原理你真的了解吗？
date: 2019-01-05 15:05:50+08:00
categories: ["Android源码分析"]
source_name: "【重拾Handler】——postDelayed原理你真的了解吗？"
jianshu_views: 7249
jianshu_url: "https://www.jianshu.com/p/f5136d8e0740"
---
>Handler已经算是一个老生常谈的知识点，但是最近在回顾的源码的时候，发现Handler其实远不止当初看源码想象的那么简单。
### 前言
本篇博客将对postDelayed的原理进行分析，起初我以为这块并不需要费过多的精力，但是事情往往需要结合实例，如下面一段代码
```
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {

            }
        }, 500);
        handler.post(new Runnable() {
            @Override
            public void run() {

            }
        });
```
可以看到这里利用Hanlder连续发送了两个消息，其中第一个是延时了500ms，哪这种情况下的Handler是怎么执行的？这时候我就犯嘀咕了，可能心里明白，但是嘴上不能说清，这时候就说明需要翻看一下源码了。
### 源码分析
```
    public final boolean postDelayed(Runnable r, long delayMillis)
    {
        return sendMessageDelayed(getPostMessage(r), delayMillis);
    }
    
        public final boolean sendMessageDelayed(Message msg, long delayMillis)
    {
        if (delayMillis < 0) {
            delayMillis = 0;
        }
        return sendMessageAtTime(msg, SystemClock.uptimeMillis() + delayMillis);
    }
```
这里首先可以看到，我们利用postDelayed时，传入的时间，最后都会和当前的时间做加和的，而不是单纯的只是用延时时间。
熟悉Handler机制的应该都明白，当我们利用Handler发送消息时，最后的实质都会向MessageQueue插入消息了,最终都会执行到enqueueMessage方法。
```
    boolean enqueueMessage(Message msg, long when) {
    	...
        synchronized (this) {
            ...
            msg.markInUse();
            msg.when = when;
            Message p = mMessages;
            boolean needWake;
            if (p == null || when == 0 || when < p.when) {
                // New head, wake up the event queue if blocked.
                //当延时时间小于当前链表头到消息的执行时间
                msg.next = p;
                mMessages = msg;
                needWake = mBlocked;
            } else {
                // Inserted within the middle of the queue.  Usually we don't have to wake
                // up the event queue unless there is a barrier at the head of the queue
                // and the message is the earliest asynchronous message in the queue.
                needWake = mBlocked && p.target == null && msg.isAsynchronous();
                Message prev;
                for (;;) {
                    prev = p;
                    p = p.next;
                    if (p == null || when < p.when) {
                    	//遍历找到合适的插入时间
                        break;
                    }
                    if (needWake && p.isAsynchronous()) {
                        needWake = false;
                    }
                }
                //插入消息链表
                msg.next = p; // invariant: p == prev.next
                prev.next = msg;
            }

            // We can assume mPtr != 0 because mQuitting is false.
            //唤醒休眠
            if (needWake) {
                nativeWake(mPtr);
            }
        }
        return true;
    }
```
这里可以看到，最核心的判断条件
```
if (p == null || when == 0 || when < p.when) {
            // New head, wake up the event queue if blocked.
            //当延时时间小于当前链表头到消息的执行时间
        } else {
        //延时比链表头的时间要长
        }
```
这里拿插入的消息的延时和当前链表头的时间点对比，如果比当前链表头的时间靠前，则新插入的消息变为新的消息头，如果比链表头的要长，则可以看到，这里利用`for`循环遍历寻找合适的时间点，也就是时间比当前要插入的延时还要长的时间点，将新插入的消息插入到这个位置。
所以这里可以先得出一个**结论**：
>延时消息会和当前消息队列里的消息头的执行时间做对比，如果比头的时间靠前，则会做为新的消息头，不然则会从消息头开始向后遍历，找到合适的位置插入延时消息。

后面这个判断也是非常重要
```
if (needWake) {
                nativeWake(mPtr);
            }
```
这里是用于判断Handler是否需要唤醒休眠等待消息的执行的，具体判断条件可以看出是和`needWake `变量有关。可以看到，这里`needWake `变量是和`mBlocked `这个变量的值密切相关。这里我们来看一下`mBlocked`变量的定义。
```
// Indicates whether next() is blocked waiting in pollOnce() with a non-zero timeout.
    private boolean mBlocked;
```
通过注释可以先简单的理解一下，这个变量是表明在执行`next()`方法是否在等待一个有延时的消息而被阻塞。既然提到了`next()`方法，我们肯定要看一下这个方法。
```
Message next() {
        // Return here if the message loop has already quit and been disposed.
        // This can happen if the application tries to restart a looper after quit
        // which is not supported.
        final long ptr = mPtr;
        if (ptr == 0) {
            return null;
        }

        int pendingIdleHandlerCount = -1; // -1 only during first iteration
        int nextPollTimeoutMillis = 0;
        for (;;) {
            if (nextPollTimeoutMillis != 0) {
                Binder.flushPendingCommands();
            }
            //native层休眠
            nativePollOnce(ptr, nextPollTimeoutMillis);

            synchronized (this) {
                // Try to retrieve the next message.  Return if found.
                final long now = SystemClock.uptimeMillis();
                Message prevMsg = null;
                Message msg = mMessages;
                if (msg != null && msg.target == null) {
                    // Stalled by a barrier.  Find the next asynchronous message in the queue.
                    do {
                        prevMsg = msg;
                        msg = msg.next;
                    } while (msg != null && !msg.isAsynchronous());
                }
                if (msg != null) {
                    if (now < msg.when) {
                    	//如果当前消息头是延时消息，比当前时间长的话，计算延时等待的时间并赋值给nextPollTimeoutMillis
                        // Next message is not ready.  Set a timeout to wake up when it is ready.
                        nextPollTimeoutMillis = (int) Math.min(msg.when - now, Integer.MAX_VALUE);
                    } else {
                    //取出消息头，执行
                        // Got a message.
                        //将mBlocked设置为false
                        mBlocked = false;
                        if (prevMsg != null) {
                            prevMsg.next = msg.next;
                        } else {
                            mMessages = msg.next;
                        }
                        msg.next = null;
                        if (DEBUG) Log.v(TAG, "Returning message: " + msg);
                        msg.markInUse();
                        return msg;
                    }
                } else {
                    // No more messages.
                    nextPollTimeoutMillis = -1;
                }

                // Process the quit message now that all pending messages have been handled.
                if (mQuitting) {
                    dispose();
                    return null;
                }

                // If first time idle, then get the number of idlers to run.
                // Idle handles only run if the queue is empty or if the first message
                // in the queue (possibly a barrier) is due to be handled in the future.
                if (pendingIdleHandlerCount < 0
                        && (mMessages == null || now < mMessages.when)) {
                    pendingIdleHandlerCount = mIdleHandlers.size();
                }
                if (pendingIdleHandlerCount <= 0) {
                    // No idle handlers to run.  Loop and wait some more.
                    //没有IdleHandler，则将mBlocked设置为true
                    mBlocked = true;
                    continue;
                }

                if (mPendingIdleHandlers == null) {
                    mPendingIdleHandlers = new IdleHandler[Math.max(pendingIdleHandlerCount, 4)];
                }
                mPendingIdleHandlers = mIdleHandlers.toArray(mPendingIdleHandlers);
            }

            // Run the idle handlers.
            // We only ever reach this code block during the first iteration.
            for (int i = 0; i < pendingIdleHandlerCount; i++) {
                final IdleHandler idler = mPendingIdleHandlers[i];
                mPendingIdleHandlers[i] = null; // release the reference to the handler

                boolean keep = false;
                try {
                    keep = idler.queueIdle();
                } catch (Throwable t) {
                    Log.wtf(TAG, "IdleHandler threw exception", t);
                }

                if (!keep) {
                    synchronized (this) {
                        mIdleHandlers.remove(idler);
                    }
                }
            }

            // Reset the idle handler count to 0 so we do not run them again.
            pendingIdleHandlerCount = 0;

            // While calling an idle handler, a new message could have been delivered
            // so go back and look again for a pending message without waiting.
            nextPollTimeoutMillis = 0;
        }
    }
```
这里可以看到几个我着重注释到地方
* 1. `nativePollOnce(ptr, nextPollTimeoutMillis);`会根据`nextPollTimeoutMillis `的值确定是否休眠，如果此时`nextPollTimeoutMillis `的值大于0，则`next()`方法会在这里休眠等待唤醒。
* 2. 从消息头取消息会和当前时间做对比，如果需要延时，则计算延时时间，并赋值给nextPollTimeoutMillis。
* 3. 如果不需要延时，则正常取出消息头，并将mBlocked设置为false
* 4. 如果idleHandler数量为0，则将mBlocked设置为true。
### 实际场景
所以到此我们可以结合实际场景分析一下Handler对于postDelayed的原理。
#### 1.消息队列中目前没有消息，然后postDelay一个延时消息。
由于消息队列目前没有消息，所以在执行`next()`方法时
```
if (msg != null) {
                  ...
                } else {
                    // No more messages.
                    nextPollTimeoutMillis = -1;
                }
```
会将`nextPollTimeoutMillis `设置为-1,而且由于没有idleHandler，所以mBlocked=true。
这时，for循环再执行到`nativePollOnce(ptr, nextPollTimeoutMillis);`则会休眠等待唤醒。
此时postDelayed发送一个消息,再执行`enqueueMessage`方法时，
```
if (p == null || when == 0 || when < p.when) {
                // New head, wake up the event queue if blocked.
                msg.next = p;
                mMessages = msg;
                needWake = mBlocked;
            } else {
                // Inserted within the middle of the queue.  Usually we don't have to wake
                // up the event queue unless there is a barrier at the head of the queue
                // and the message is the earliest asynchronous message in the queue.
                needWake = mBlocked && p.target == null && msg.isAsynchronous();
                Message prev;
                for (;;) {
                    prev = p;
                    p = p.next;
                    if (p == null || when < p.when) {
                        break;
                    }
                    if (needWake && p.isAsynchronous()) {
                        needWake = false;
                    }
                }
                msg.next = p; // invariant: p == prev.next
                prev.next = msg;
            }
 // We can assume mPtr != 0 because mQuitting is false.
            if (needWake) {
                nativeWake(mPtr);
            }
```
由于当前的头消息为null，所以新插入的延时消息直接作为头消息，而mBlocked=true，所以needWake=true
所以变会执行`nativeWake(mPtr);`方法，底层唤醒休眠，这时`next()`方法变会从`nativePollOnce(ptr, nextPollTimeoutMillis);`唤醒，继续取消息执行。
这里可能有人有疑问，**这时取消息，便是我们插入的延时消息，那么肯定又休眠等待唤醒了，此时如果没有新的消息插入，谁来唤醒延时消息执行呢？**
这里`nativePollOnce(ptr, nextPollTimeoutMillis);`其实是有自动的唤醒机制的，也就是说除了利用`nativeWake(mPtr);`被动唤醒，底层自动也会唤醒自身执行延时消息的。
#### 2.消息队列中没有消息，先插入一个延时消息，再插入一个正常的不延时的消息。
这个场景就可以接着上面那个分析，当插入一个延时消息后，会进入休眠等待的过程，这时mBlocked=true，这时再插入一个消息。
```
if (p == null || when == 0 || when < p.when) {
                // New head, wake up the event queue if blocked.
                msg.next = p;
                mMessages = msg;
                needWake = mBlocked;
            } else {
                // Inserted within the middle of the queue.  Usually we don't have to wake
                // up the event queue unless there is a barrier at the head of the queue
                // and the message is the earliest asynchronous message in the queue.
                needWake = mBlocked && p.target == null && msg.isAsynchronous();
                Message prev;
                for (;;) {
                    prev = p;
                    p = p.next;
                    if (p == null || when < p.when) {
                        break;
                    }
                    if (needWake && p.isAsynchronous()) {
                        needWake = false;
                    }
                }
                msg.next = p; // invariant: p == prev.next
                prev.next = msg;
            }

            // We can assume mPtr != 0 because mQuitting is false.
            if (needWake) {
                nativeWake(mPtr);
            }
```
由于此时消息头是延时消息，新插入的消息不是延时消息，肯定比延时消息的时间小，所以新插入的消息替换延时消息，变成新的消息头，并且needWake=mBlocked=true，所以会执行`nativeWake(mPtr);`方法，唤醒休眠，这时再执行`next()`方法中的for循环，便会取消息头，就会取到新插入的不需要延时的消息，并执行，接着由于后面的消息就是延时消息，所以会进行新一轮的休眠等待。
### 拓展
基于以上的分析其实大家对于Handler肯定又有了一个更新的认识，这里再拓展几个问题：
#### Handler的休眠具体指的什么？会不会阻塞UI？
这里就涉及到Linux pipe/epoll机制，简单说就是在主线程的MessageQueue没有消息时，便阻塞在loop的queue.next()中的nativePollOnce()方法里，此时主线程会释放CPU资源进入休眠状态，直到下个消息到达或者有事务发生，通过往pipe管道写端写入数据来唤醒主线程工作。这里采用的epoll机制，是一种IO多路复用机制，可以同时监控多个描述符，当某个描述符就绪(读或写就绪)，则立刻通知相应程序进行读或写操作，本质同步I/O，即读写是阻塞的。 所以说，主线程大多数时候都是处于休眠状态，并不会消耗大量CPU资源。
#### Handler的Delay不一定会在when的时间执行
（1）在Loop.loop()中是顺序处理消息，如果前一个消息处理耗时较长，完成之后已经超过了when，消息不可能在when时间点被处理。
（2）即使when的时间点没有被处理其他消息所占用，线程也有可能被调度失去cpu时间片。
（3）在等待时间点when的过程中有可能入队处理时间更早的消息，会被优先处理，又增加了（1）的可能性。
所以由上述三点可知，Handler提供的指定处理时间的api诸如postDelayed()/postAtTime()/sendMessageDelayed()/sendMessageAtTime()，只能保证在指定时间之前不被执行，不能保证在指定时间点被执行。

### 相关博客推荐
[postDelayed原理](http://www.dss886.com/2016/08/17/01/)
[Handler管道的原理](http://wangkuiwu.github.io/2014/08/26/MessageQueue/#anchor1)
