>1.[EventBus源码解析（一）—订阅过程](https://www.jianshu.com/p/2e0182991ac9)
>2.[EventBus源码解析（二）—发布事件和注销流程](https://www.jianshu.com/p/ebec755ce098)
>3.[EventBus源码解析（三）—进阶源码](https://www.jianshu.com/p/ca36147d910a)

## 前言
前两篇博客对EventBus的基本使用的流程进行了源码分析，其实看完前两篇博客，对于EventBus的源码可以说已经有了**70%**的理解了（个人认为哈），本篇博客主要对我认为的几个EventBus进阶使用的方面进行源码分析，为EventBus源码分析系列结个尾。
## 目录
* 1.粘性事件
* 2.多线程
* 3.编译期注解优化（EventBus3.0上的一大重要优化）

## 源码分析
### 粘性事件
粘性事件的用法这里就不做介绍了，但是使用场景却是非常多，比如如下场景：
>Activity跳转时传递数据一般都是使用Intent携带Bundle数据进行传递，但Intent携带Bundle有时会有一些意想不到的bug（常见的就是Bundle数据过大），当Activity跳转使用EventBus进行传递数据，这时就需要使用**粘性事件**

**粘性事件的特点**：发送者发送了粘性事件后，若有订阅者则会被订阅者触发，若此时无订阅者，该事件会被保留，当有新的订阅该事件的订阅者出现，新的订阅者则会触发该事件。（粘性事件可以被前订阅者触发后移除，后面的订阅者就无法拿到粘性事件）

**源码分析**
首先来看一下发送粘性事件的方法`postSticky`
```
public void postSticky(Object event) {
        synchronized (stickyEvents) {
            stickyEvents.put(event.getClass(), event);
        }
        // Should be posted after it is putted, in case the subscriber wants to remove immediately
        post(event);
    }
```
源码很好理解，这里的`stickyEvents`是一个`ConcurrentHashMap`，当我们发送粘性事件后，事件会先被put到该map中保存，接着才会触发`post`方法发送事件，关于post方法发送事件的源码分析具体可以见[第二篇博客](https://www.jianshu.com/p/ebec755ce098)。
接着我们来看一下订阅粘性事件的方法，看过[第一篇博客](https://www.jianshu.com/p/2e0182991ac9)的提到了，当调用`register`方法订阅后，会调用`subscribe`方法。
```
private void subscribe(Object subscriber, SubscriberMethod subscriberMethod) {
        ...

        if (subscriberMethod.sticky) {
            if (eventInheritance) {
                //是否设置了事件继承，默认是true
                // Existing sticky events of all subclasses of eventType have to be considered.
                // Note: Iterating over all events may be inefficient with lots of sticky events,
                // thus data structure should be changed to allow a more efficient lookup
                // (e.g. an additional map storing sub classes of super classes: Class -> List<Class>).
                Set<Map.Entry<Class<?>, Object>> entries = stickyEvents.entrySet();
                for (Map.Entry<Class<?>, Object> entry : entries) {
                    Class<?> candidateEventType = entry.getKey();
                    if (eventType.isAssignableFrom(candidateEventType)) {
                        //事件class和事件对象相同，或是子类
                        Object stickyEvent = entry.getValue();
                        //通过反射发送粘性事件
                        checkPostStickyEventToSubscription(newSubscription, stickyEvent);
                    }
                }
            } else {
                Object stickyEvent = stickyEvents.get(eventType);
                //通过反射发送粘性事件
                checkPostStickyEventToSubscription(newSubscription, stickyEvent);
            }
        }
    }
```
可以看到这里判断订阅的方法是订阅的粘性事件后，处理事件继承的相关逻辑和常规事件是相同逻辑，具体可以看[第一篇博客](https://www.jianshu.com/p/2e0182991ac9)，所以这里可以看到最后都是走的`checkPostStickyEventToSubscription `。而`checkPostStickyEventToSubscription `方法里面做了一些判空处理直接走的是`postToSubscription`，所以走的和常规事件是完全一摸一样的逻辑，最后都是调用反射调用订阅方法。具体可以看[第二篇博客](https://www.jianshu.com/p/ebec755ce098)
最后提一点，我们如果需要截断粘性事件，可以在需要截断的方法内调用`removeStickyEvent`方法。
```
public <T> T removeStickyEvent(Class<T> eventType) {
        synchronized (stickyEvents) {
            return eventType.cast(stickyEvents.remove(eventType));
        }
    }
```
### 多线程
EventBus是支持多线程之间的调用的，虽然可能不是特别常用，但是EventBus的多线程的实现原来还是很值得我们研究学习的。其实要研究EventBus的多线程，我们主要关注`postToSubscription`方法。
```
private void postToSubscription(Subscription subscription, Object event, boolean isMainThread) {
        switch (subscription.subscriberMethod.threadMode) {
            //默认类型
            case POSTING:
                invokeSubscriber(subscription, event);
                break;
            case MAIN:
                if (isMainThread) {
                    //如果当前就在UI线程，则直接反射执行
                    invokeSubscriber(subscription, event);
                } else {
                    mainThreadPoster.enqueue(subscription, event);
                }
                break;
            case MAIN_ORDERED:
                //不同于MAIN，直接通过Handler的队列执行，串行的
                if (mainThreadPoster != null) {
                    mainThreadPoster.enqueue(subscription, event);
                } else {
                    // temporary: technically not correct as poster not decoupled from subscriber
                    invokeSubscriber(subscription, event);
                }
                break;
            case BACKGROUND:
                if (isMainThread) {
                    //如果当前是UI线程，则异步
                    backgroundPoster.enqueue(subscription, event);
                } else {
                    //不是UI线程，则在该线程执行
                    invokeSubscriber(subscription, event);
                }
                break;
            case ASYNC:
                asyncPoster.enqueue(subscription, event);
                break;
            default:
                throw new IllegalStateException("Unknown thread mode: " + subscription.subscriberMethod.threadMode);
        }
    }
```
这里可以看到分为了五种case，其中第一种就是我们最常用的类型，就是发送事件和接收事件都在主线程。而第二种`MAIN`和第三种`MAIN_ORDERED`仔细看会发现只是调用顺序不同，这其实也是这两种的区别。
>**MAIN**：如果是主线程中调用则会直接执行`invokeSubscriber `反射调用订阅方法，如果不是主线程，则会调用`mainThreadPoster.enqueue`将事件加入队列，顺序执行，所以我们会发现，主线程会有**特殊直达通道**
>**MAIN_ORDERED**：只要mainThreadPoster不会空，无论是主线程还是其他任何子线程，所有的事件都会统一调用`mainThreadPoster.enqueue`将事件加入队列，顺序执行，保证事件顺序。
这时我们会好奇`mainThreadPoster`是个什么对象了
```
EventBus(EventBusBuilder builder) {
        mainThreadSupport = builder.getMainThreadSupport();
        mainThreadPoster = mainThreadSupport != null ? mainThreadSupport.createPoster(this) : null;
        ...
    }
```
可以看到，`mainThreadPoster`的是否初始化是由`mainThreadSupport `变量确定的。
```
MainThreadSupport getMainThreadSupport() {
        if (mainThreadSupport != null) {
            return mainThreadSupport;
        } else if (AndroidLogger.isAndroidLogAvailable()) {
            Object looperOrNull = getAndroidMainLooperOrNull();
            return looperOrNull == null ? null :
                    new MainThreadSupport.AndroidHandlerMainThreadSupport((Looper) looperOrNull);
        } else {
            return null;
        }
    }
====================================================================
    Object getAndroidMainLooperOrNull() {
        try {
            return Looper.getMainLooper();
        } catch (RuntimeException e) {
            // Not really a functional Android (e.g. "Stub!" maven dependencies)
            return null;
        }
    }
```

可以看到这里如果`getAndroidMainLooperOrNull`不为空，则返回`MainThreadSupport.AndroidHandlerMainThreadSupport((Looper) looperOrNull)`构建的对象。而`getAndroidMainLooperOrNull `可以看到返回的是主线程的Looper对象。所以这里就很好理解了。
而`mainThreadPoster `是通过`mainThreadSupport.createPoster(this)`方法创建的。

```
public interface MainThreadSupport {

    boolean isMainThread();

    Poster createPoster(EventBus eventBus);

    class AndroidHandlerMainThreadSupport implements MainThreadSupport {
		.....
        @Override
        public Poster createPoster(EventBus eventBus) {
            //在主线程的Handler
            return new HandlerPoster(eventBus, looper, 10);
        }
    }

}
```
可以发现，拿到了主线程的Looper后我们返回的其实一个实现了Poster接口的`Handler`对象`HandlerPoster`对象给`mainThreadPoster`。
```
public class HandlerPoster extends Handler implements Poster {

    private final PendingPostQueue queue;
    private final int maxMillisInsideHandleMessage;
    private final EventBus eventBus;
    private boolean handlerActive;

    protected HandlerPoster(EventBus eventBus, Looper looper, int maxMillisInsideHandleMessage) {
        super(looper);
        this.eventBus = eventBus;
        this.maxMillisInsideHandleMessage = maxMillisInsideHandleMessage;
        //用java实现的一个队列
        queue = new PendingPostQueue();
    }

    public void enqueue(Subscription subscription, Object event) {
        //内部有一个ArrayList,没有就new
        PendingPost pendingPost = PendingPost.obtainPendingPost(subscription, event);
        synchronized (this) {
            //入队
            queue.enqueue(pendingPost);
            if (!handlerActive) {
                handlerActive = true;
                //发送消息
                if (!sendMessage(obtainMessage())) {
                    throw new EventBusException("Could not send handler message");
                }
            }
        }
    }

    @Override
    public void handleMessage(Message msg) {
        boolean rescheduled = false;
        try {
            long started = SystemClock.uptimeMillis();
            while (true) {
                //出队列
                PendingPost pendingPost = queue.poll();
                if (pendingPost == null) {
                    synchronized (this) {
                        // Check again, this time in synchronized
                        //再获取一次
                        pendingPost = queue.poll();
                        //仍然为null则return
                        if (pendingPost == null) {
                            handlerActive = false;
                            return;
                        }
                    }
                }
                //反射调用
                eventBus.invokeSubscriber(pendingPost);
                long timeInMethod = SystemClock.uptimeMillis() - started;
                //如果超过maxMillisInsideHandleMessage还没执行完则重新调度
                if (timeInMethod >= maxMillisInsideHandleMessage) {
                    if (!sendMessage(obtainMessage())) {
                        throw new EventBusException("Could not send handler message");
                    }
                    rescheduled = true;
                    return;
                }
            }
        } finally {
            handlerActive = rescheduled;
        }
    }
}
```
这里通过源码我们发现，`HandlerPoster`继承了`Handler`,内部维护了一个队列用于存放事件。上面的注释也写的很清楚了，其实原理就是利用`Handler`的实现机制，在收到事件的时候，先将事件放到队列中，然后发送一条消息，在`handleMessage`里收到消息后，在从队列中拿去消息，并且最终还是调用`eventBus.invokeSubscriber(pendingPost)`反射，调用方法。
**BACKGROUND**
```
case BACKGROUND:
                if (isMainThread) {
                    //如果当前是UI线程，则异步
                    backgroundPoster.enqueue(subscription, event);
                } else {
                    //不是UI线程，则在该线程执行
                    invokeSubscriber(subscription, event);
                }
                break;
```
这种情况，其实发送事件的线程不是主线程，就直接在该线程执行，如果是主线程，则异步执行。其中`backgroundPoster`在默认构造函数中默认创建。
```
final class BackgroundPoster implements Runnable, Poster {

    private final PendingPostQueue queue;
    private final EventBus eventBus;

    private volatile boolean executorRunning;

    BackgroundPoster(EventBus eventBus) {
        this.eventBus = eventBus;
        queue = new PendingPostQueue();
    }

    public void enqueue(Subscription subscription, Object event) {
        PendingPost pendingPost = PendingPost.obtainPendingPost(subscription, event);
        synchronized (this) {
            queue.enqueue(pendingPost);
            //可以看到在线程池中是串行的，执行完一个，才会变为false
            if (!executorRunning) {
                executorRunning = true;
                //EventBus默认的线程池是newCachedThreadPool,无限大的可复用线程池
                eventBus.getExecutorService().execute(this);
            }
        }
    }

    @Override
    public void run() {
        try {
            try {
                while (true) {
                    PendingPost pendingPost = queue.poll(1000);
                    if (pendingPost == null) {
                        synchronized (this) {
                            // Check again, this time in synchronized
                            //消费者生产者模型
                            pendingPost = queue.poll();
                            if (pendingPost == null) {
                                executorRunning = false;
                                return;
                            }
                        }
                    }
                    //反射执行
                    eventBus.invokeSubscriber(pendingPost);
                }
            } catch (InterruptedException e) {
                eventBus.getLogger().log(Level.WARNING, Thread.currentThread().getName() + " was interruppted", e);
            }
        } finally {
            executorRunning = false;
        }
    }

}
```
可以发现`BackgroundPoster`实现了Runnable接口，内部也同样维护了一个队列，这里要注意的有两点：
>1.我们会发现执行该runnable的是使用的是EventBus内部的一个线程池，newCachedThreadPool,无限大的可复用线程池。
>2.这里其实是一个很规范的消费者生产者模型，所以我们会发现所有的事件都是顺序执行的，也就是串行的。

**ASYNC**
```
case ASYNC:
                asyncPoster.enqueue(subscription, event);
                break;
                
===============================================================
class AsyncPoster implements Runnable, Poster {

    private final PendingPostQueue queue;
    private final EventBus eventBus;

    AsyncPoster(EventBus eventBus) {
        this.eventBus = eventBus;
        queue = new PendingPostQueue();
    }

    public void enqueue(Subscription subscription, Object event) {
        PendingPost pendingPost = PendingPost.obtainPendingPost(subscription, event);
        queue.enqueue(pendingPost);
        //和Background一样的是newCachedThreadPool，但是没有了串行的限制，是并行的，来一个new一个线程，无限制
        eventBus.getExecutorService().execute(this);
    }

    @Override
    public void run() {
        PendingPost pendingPost = queue.poll();
        if(pendingPost == null) {
            throw new IllegalStateException("No pending post available");
        }
        //反射执行
        eventBus.invokeSubscriber(pendingPost);
    }

}

```
而对于ASYNC这种情况，我们就会发现，原理上也是用EventBus默认的线程池进行异步执行，但是这里就没有了串行的限制，而是并行的，也就是所有的事件是没有先后顺序的。这是和`BACKGROUND`的区别。
### 编译期注解
其实这是EventBus3.0相比于2.0非常大的区别和优化，EventBus可以说使用起来非常方便，但是通过前面这么多的分析，大家也会发现，EventBus有一个让人很担心的地方，就是过多的使用**反射**，这对于客户端性能来说是一个很不好的消息。于是EventBus3.0相较于2.0引入了注解，而且是**编译期注解**，这项技术可以说是知名框架必备属性（ButterKnife,Dragger等）。对于**编译期注解**，这里不做过多的解释，但是非常建议大家自己动手学习使用一下。这里放上几篇我认为不错的博客推荐给大家吧：(可能要翻墙)
[Java注解处理器](https://www.race604.com/annotation-processing/)
[编译时注解处理方](http://pyonhu.com/2017/02/10/bian-yi-shi-zhu-jie-chu-li-fang/)
**简单分析源码**
这里我们还是来简单分析一下源码吧，首先我们当我们使用了EventBus的编译期注解后（关于EventBus生成索引的方法网上有很多介绍），编译后我们会发现会在`\ProjectName\app\build\generated\source\apt\PakageName\`目录下生成一个名为`MyEventBusIndex `的索引类。
```
public class MainActivity extends BaseActivity {
	.....
    @Subscribe
    public void onEventMain(Child integer) {
        Log.i("--------", "---------");
    }

    @Subscribe
    public void onEventMain(Parent integer) {
        Log.i("--------", "---------");
    }

    @Subscribe
    public void onEven1tMain(Integer integer) {
        Log.i("--------", "1");
    }

    @Subscribe
    public void onEven2tMain(Integer integer) {
        Log.i("--------", "2");
    }

}
```
以上是我们测试写的MainActivity，并且使用了EventBus，有四个订阅方法。
```
package com.example.xuan.nouse;

import org.greenrobot.eventbus.meta.SimpleSubscriberInfo;
import org.greenrobot.eventbus.meta.SubscriberMethodInfo;
import org.greenrobot.eventbus.meta.SubscriberInfo;
import org.greenrobot.eventbus.meta.SubscriberInfoIndex;

import org.greenrobot.eventbus.ThreadMode;

import java.util.HashMap;
import java.util.Map;

/** This class is generated by EventBus, do not edit. */
public class MyEventBusIndex implements SubscriberInfoIndex {
    private static final Map<Class<?>, SubscriberInfo> SUBSCRIBER_INDEX;

    static {
        SUBSCRIBER_INDEX = new HashMap<Class<?>, SubscriberInfo>();

        putIndex(new SimpleSubscriberInfo(MainActivity.class, true, new SubscriberMethodInfo[] {
            new SubscriberMethodInfo("onEventMain", com.example.xuan.nouse.model.Child.class),
            new SubscriberMethodInfo("onEventMain", Parent.class),
            new SubscriberMethodInfo("onEven1tMain", Integer.class),
            new SubscriberMethodInfo("onEven2tMain", Integer.class),
        }));

    }

    private static void putIndex(SubscriberInfo info) {
        SUBSCRIBER_INDEX.put(info.getSubscriberClass(), info);
    }

    @Override
    public SubscriberInfo getSubscriberInfo(Class<?> subscriberClass) {
        SubscriberInfo info = SUBSCRIBER_INDEX.get(subscriberClass);
        if (info != null) {
            return info;
        } else {
            return null;
        }
    }
}

```
可以发现，自动生成的类也很简单，就是将我们的订阅信息，放入了一个静态的Map中。大家可能对于上面生成的类没有太注意看，这里有一个需要注意的点，**对于其他包内的类，EventBus是如果引入的**。
`new SubscriberMethodInfo("onEventMain", com.example.xuan.nouse.model.Child.class)`
回头看一下，我们会发现，使用的是全类名。
关于EventBus的注解处理器，我们需要看`EventBusAnnotationProcessor`类，主要关注`process`方法（建议仔细学习阅读编译期注解的相关博客后阅读）。在一系列判断后，最后会进入`createInfoIndexFile`方法，用于创建文件，
```
private void createInfoIndexFile(String index) {
        BufferedWriter writer = null;
        try {
            JavaFileObject sourceFile = processingEnv.getFiler().createSourceFile(index);
            int period = index.lastIndexOf('.');
            String myPackage = period > 0 ? index.substring(0, period) : null;
            String clazz = index.substring(period + 1);
            writer = new BufferedWriter(sourceFile.openWriter());
            if (myPackage != null) {
                writer.write("package " + myPackage + ";\n\n");
            }
            writer.write("import org.greenrobot.eventbus.meta.SimpleSubscriberInfo;\n");
            writer.write("import org.greenrobot.eventbus.meta.SubscriberMethodInfo;\n");
            writer.write("import org.greenrobot.eventbus.meta.SubscriberInfo;\n");
            writer.write("import org.greenrobot.eventbus.meta.SubscriberInfoIndex;\n\n");
            writer.write("import org.greenrobot.eventbus.ThreadMode;\n\n");
            writer.write("import java.util.HashMap;\n");
            writer.write("import java.util.Map;\n\n");
            writer.write("/** This class is generated by EventBus, do not edit. */\n");
            writer.write("public class " + clazz + " implements SubscriberInfoIndex {\n");
            writer.write("    private static final Map<Class<?>, SubscriberInfo> SUBSCRIBER_INDEX;\n\n");
            writer.write("    static {\n");
            writer.write("        SUBSCRIBER_INDEX = new HashMap<Class<?>, SubscriberInfo>();\n\n");
            writeIndexLines(writer, myPackage);
            writer.write("    }\n\n");
            writer.write("    private static void putIndex(SubscriberInfo info) {\n");
            writer.write("        SUBSCRIBER_INDEX.put(info.getSubscriberClass(), info);\n");
            writer.write("    }\n\n");
            writer.write("    @Override\n");
            writer.write("    public SubscriberInfo getSubscriberInfo(Class<?> subscriberClass) {\n");
            writer.write("        SubscriberInfo info = SUBSCRIBER_INDEX.get(subscriberClass);\n");
            writer.write("        if (info != null) {\n");
            writer.write("            return info;\n");
            writer.write("        } else {\n");
            writer.write("            return null;\n");
            writer.write("        }\n");
            writer.write("    }\n");
            writer.write("}\n");
        } catch (IOException e) {
            throw new RuntimeException("Could not write source for " + index, e);
        } finally {
            if (writer != null) {
                try {
                    writer.close();
                } catch (IOException e) {
                    //Silent
                }
            }
        }
    }
```
没错，就是这么简单粗暴，EventBus也没有使用`JavaWriter`或者`JavaPoet`，只是单纯的字符串拼接。

## 总结
EventBus的源码分析到这里就基本上结束了，具体的建议大家自己去阅读学习，在我看来，EventBus的源码还是很值得我们亲自阅读学习的，不能有简单，知道了原理就行这种心态，就认为没必要看这个框架的源码，还是那句话`Read The Fucking Source Code`



