### 前言
一直在使用这个框架，但是一直没有注意这个框架的实现原理。使用过这款框架的人应该都知道，LeakCanary是一款能够帮助开发者检查内存泄漏的开源库，只需要简单配置，就可以当使用过程中产生内存泄漏时，弹出通知，并且可以我们可以查看详细的引用链，帮助我们进行内存泄漏的分析。
### 项目预览
![项目结构](https://upload-images.jianshu.io/upload_images/7866586-49925d220822a5e3.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
这里专门放了一张LeakCanary的项目的目录结构，可以看到，LeakCanary的项目目录还是很考究的，总体分为了5个模块，每个都专门负责一个功能。
>1.analyzer 内存泄漏分析功能模块，内存泄漏的路径分析就是该模块，**haha库**就是在该模块中使用
>2.watcher 内存泄漏监控模块，监控并且发现内存泄漏的就是该模块
>3.android 将内存泄漏监控和Android的生命周期绑定，实现Android中的内存泄漏监听
>4.android-no-op 空壳模块，实现真正发布realeas包后，不进行内存泄漏监控，损耗性能
>5.sample demo模块

从上面的分析可以看出，LeakCanary这款内存泄漏框架的目录结构真的很**考究**，按照LeakCanary的功能体积，完全没必要拆分的这么散，但是这样做，充分将LeakCanary的功能发挥到最大化，为什么这么说哪？
熟悉LeakCanary原理的都知道，LeankCanary其实是利用Java的弱引用特性，加上JVM回收一定的机制，实现内存泄漏的监控的，也就是说，LeakCanary并不是一款和Android**死绑定**的一款开源框架，所以这时候LeakCanary这样的目录结构就体现出了它的优点，我们完全可以将`watcher`模块或者`analyzer`模块拆分出来，处理其他以`Java`语言作为开发语言的项目的内存泄漏分析。
### 源码分析
还是老方式，一个好的框架肯定有一个好的外观类来统领入口，LeakCanary当然不能少，一般我们的使用方式就是：
```
protected void setupLeakCanary() {
    if (LeakCanary.isInAnalyzerProcess(this)) {
      // This process is dedicated to LeakCanary for heap analysis.
      // You should not init your app in this process.
      return;
    }
    LeakCanary.install(this);
  }
```
当然最核心的就是这句代码`LeakCanary.install(this);`前面的`LeakCanary.isInAnalyzerProcess(this)`这里先暂不分析（当然后面会分析的，这里面有一个很棒的方法）
```
public static RefWatcher install(Application application) {
    //创建RefWatcher
    return refWatcher(application).listenerServiceClass(DisplayLeakService.class)
            //设置已知的内存泄漏问题，或者系统的内存泄漏问题
        .excludedRefs(AndroidExcludedRefs.createAppDefaults().build())
        .buildAndInstall();
  }
```
这里可以看到，总体上来看分为了四个步骤：
1. 创建了RefWatcher（也就是检测内存泄漏的类）
2. 设置了内存泄漏的通知Service（通知）
3. 设置了需要忽略的已知的系统级别的内存泄漏(可以自定义)
4. 开始监听

接下来就分别看看每一个步骤。
#### 第一个步骤
```
/**
   * 创建一个builder对象
   */
  public static AndroidRefWatcherBuilder refWatcher(Context context) {
    return new AndroidRefWatcherBuilder(context);
  }
```
第一个步骤没什么好说的，创建了一个专门为Android使用的Watcher的Builder类。后面我们看的很多方法都基于这个类。
#### 第二个步骤
```
public AndroidRefWatcherBuilder listenerServiceClass(
      Class<? extends AbstractAnalysisResultService> listenerServiceClass) {
    return heapDumpListener(new ServiceHeapDumpListener(context, listenerServiceClass));
  }
  
  public ServiceHeapDumpListener(Context context,
      Class<? extends AbstractAnalysisResultService> listenerServiceClass) {
    setEnabled(context, listenerServiceClass, true);
    setEnabled(context, HeapAnalyzerService.class, true);
    this.listenerServiceClass = checkNotNull(listenerServiceClass, "listenerServiceClass");
    this.context = checkNotNull(context, "context").getApplicationContext();
  }
  
  public final T heapDumpListener(HeapDump.Listener heapDumpListener) {
    this.heapDumpListener = heapDumpListener;
    return self();
  }
  
  @SuppressWarnings("unchecked")
  protected final T self() {
    return (T) this;
  }
```
接下来这个地方还是需要我们注意到，这里new了一个`ServiceHeapDumpListener `，在`heapDumpListener `方法里将new到`listener`赋值给了`this.heapDumpListener `。
这里有一个小细节挺值得我们注意的，这里由于是**泛型**,所以不能直接返回this，这里统一返回了`self()`方法，统一在self方法里做强制转换和`unchecked`操作。
通过这里的方法我们可以知道，我们将`DisplayLeakService.class `类，设置给了`AndroidRefWatcherBuilder `的一个自定义`Listener`变量。
#### 第三个步骤:设置已知的内存泄漏问题，或者系统的内存泄漏问题
这里我们就看一下`AndroidExcludedRefs.createAppDefaults().build()`这个方法。
```
public static ExcludedRefs.Builder createAppDefaults() {
    return createBuilder(EnumSet.allOf(AndroidExcludedRefs.class));
  }
  public static ExcludedRefs.Builder createBuilder(EnumSet<AndroidExcludedRefs> refs) {
    ExcludedRefs.Builder excluded = ExcludedRefs.builder();
    for (AndroidExcludedRefs ref : refs) {
      if (ref.applies) {
        ref.add(excluded);
        ((ExcludedRefs.BuilderWithParams) excluded).named(ref.name());
      }
    }
    return excluded;
  }
```
到这里其实我们没必要在往里面继续看了，通过这两个方法，大概可以看出这个是通过遍历`AndroidExcludedRefs.class `类中定义的已知的一些系统级别的bug，得到一个集合，在后面发现内存泄漏的时候会进行忽略操作。

#### 第四个步骤:开始进行监听操作。
```
public RefWatcher buildAndInstall() {
    //只能创建一次
    if (LeakCanaryInternals.installedRefWatcher != null) {
      throw new UnsupportedOperationException("buildAndInstall() should only be called once.");
    }
    //创建RefWatcher
    RefWatcher refWatcher = build();
    if (refWatcher != DISABLED) {

      LeakCanary.enableDisplayLeakActivity(context);
      //默认为true
      if (watchActivities) {
        //注意，在这里通过监听Application,监听Activity的生命周期
        ActivityRefWatcher.install((Application) context, refWatcher);
      }
    }
    LeakCanaryInternals.installedRefWatcher = refWatcher;
    return refWatcher;
  }
```
可以看到，首先进行了判空，单例的思想还是很重要的。
下面这个`build()`方法还是很重要的。
```
public final RefWatcher build() {
    // 判断install是否在Analyzer进程里，重复执行
    if (isDisabled()) {
      return RefWatcher.DISABLED;
    }
    //用于排除某些系统bug导致的内存泄露
    ExcludedRefs excludedRefs = this.excludedRefs;
    if (excludedRefs == null) {
      excludedRefs = defaultExcludedRefs();
    }
    //用于分析生成的dump文件，找到内存泄露的原因
    HeapDump.Listener heapDumpListener = this.heapDumpListener;
    if (heapDumpListener == null) {
      heapDumpListener = defaultHeapDumpListener();
    }
    //用于查询是否正在调试中，调试中不会执行内存泄露检测
    DebuggerControl debuggerControl = this.debuggerControl;
    if (debuggerControl == null) {
      debuggerControl = defaultDebuggerControl();
    }
    //用于在产生内存泄露室执行dump 内存heap
    HeapDumper heapDumper = this.heapDumper;
    if (heapDumper == null) {
      heapDumper = defaultHeapDumper();
    }
    //执行内存泄露检测的executor
    WatchExecutor watchExecutor = this.watchExecutor;
    if (watchExecutor == null) {
      //创建默认的监听内存泄漏的线程池
      watchExecutor = defaultWatchExecutor();
    }
    //用于在判断内存泄露之前，再给一次GC的机会
    GcTrigger gcTrigger = this.gcTrigger;
    if (gcTrigger == null) {
      gcTrigger = defaultGcTrigger();
    }

    return new RefWatcher(watchExecutor, debuggerControl, gcTrigger, heapDumper, heapDumpListener,
        excludedRefs);
  }
```
这个build方法这里我们需要注意，我们在最开始的生成了`AndroidRefWatcherBuilder`,这个是继承于`RefWatcherBuilder`类的，但是这里的`build()`方法是父类的方法，也就是`RefWatcherBuilder`的方法，但是在`build()`内的许多调用都是`AndroidRefWatcherBuilder `重写的方法。
首先来看第一个方法`isDisabled()`
```
@Override protected boolean isDisabled() {
    //用于判断服务进程是否在前台，重要
    return LeakCanary.isInAnalyzerProcess(context);
  }
```
可以看到，这里又用到了我们前面提到的一个方法，是用于判断当前进程是否在前台，这里因为分析主流程，所以先不做分析。
```
@Override protected ExcludedRefs defaultExcludedRefs() {
    return AndroidExcludedRefs.createAppDefaults().build();
  }
```
接下来看到是设置了Android特有的一些系统的内存泄漏，和前面分析的一致。
```
//用于分析生成的dump文件，找到内存泄露的原因
    HeapDump.Listener heapDumpListener = this.heapDumpListener;
    if (heapDumpListener == null) {
      heapDumpListener = defaultHeapDumpListener();
    }
    @Override protected HeapDump.Listener defaultHeapDumpListener() {
    return new ServiceHeapDumpListener(context, DisplayLeakService.class);
  }
```
因为在`install()`方法中已经设置了用于发送内存泄漏通知的Service，这里变不为`null`，不然其实`default`的和初始化的也是相同的。
```
//用于查询是否正在调试中，调试中不会执行内存泄露检测
    DebuggerControl debuggerControl = this.debuggerControl;
    if (debuggerControl == null) {
      debuggerControl = defaultDebuggerControl();
    }
    
    @Override protected DebuggerControl defaultDebuggerControl() {
    return new AndroidDebuggerControl();
  }
  
  public final class AndroidDebuggerControl implements DebuggerControl {
  @Override public boolean isDebuggerAttached() {
    return Debug.isDebuggerConnected();
  }
}
```
这里其实也挺值得我们学习的，这里当是调试的时候，便不会进行内存泄漏检测，而如何确定是在进行调试，这里可以看到使用了`Debug.isDebuggerConnected()`方法。
```
//用于在产生内存泄露室执行dump 内存heap
    HeapDumper heapDumper = this.heapDumper;
    if (heapDumper == null) {
      heapDumper = defaultHeapDumper();
    }
    
    @Override protected HeapDumper defaultHeapDumper() {
    LeakDirectoryProvider leakDirectoryProvider = new DefaultLeakDirectoryProvider(context);
    return new AndroidHeapDumper(context, leakDirectoryProvider);
  }
```
这里就是生产内存泄漏的文件的。
```
//执行内存泄露检测的executor
    WatchExecutor watchExecutor = this.watchExecutor;
    if (watchExecutor == null) {
      //创建默认的监听内存泄漏的线程池
      watchExecutor = defaultWatchExecutor();
    }
    
    @Override protected WatchExecutor defaultWatchExecutor() {
    //默认线程池，5s
    return new AndroidWatchExecutor(DEFAULT_WATCH_DELAY_MILLIS);
  }
  
  public AndroidWatchExecutor(long initialDelayMillis) {
    //主线程Handler
    mainHandler = new Handler(Looper.getMainLooper());
    //这里new了一个HandlerThread，也就是一个异步线程，内部封装好了looper.prepare()等操作
    HandlerThread handlerThread = new HandlerThread(LEAK_CANARY_THREAD_NAME);
    handlerThread.start();
    //handlerThread内部的handler
    backgroundHandler = new Handler(handlerThread.getLooper());
    this.initialDelayMillis = initialDelayMillis;
    maxBackoffFactor = Long.MAX_VALUE / initialDelayMillis;
  }
```
可以看到这里虽然叫做看似像是线程池，其实也是利用了`Android`官方的基础组件，这里可以看到**快速**的创建了一个**主现场**的`handler`和一个`HanlderThread`,和`HandlerThread`内部的`Handler`。具体`HanlderThread`是什么，这里放上这个类。
```
/**
 * Handy class for starting a new thread that has a looper. The looper can then be 
 * used to create handler classes. Note that start() must still be called.
 */
public class HandlerThread extends Thread {
@Override
    public void run() {
        mTid = Process.myTid();
        Looper.prepare();
        synchronized (this) {
            mLooper = Looper.myLooper();
            notifyAll();
        }
        Process.setThreadPriority(mPriority);
        onLooperPrepared();
        Looper.loop();
        mTid = -1;
    }
}
```
可以看到就是一个`Thread`只不过内部封装好了`Android`使用多线程Hanlder的一系列操作。
```
//用于在判断内存泄露之前，再给一次GC的机会
    GcTrigger gcTrigger = this.gcTrigger;
    if (gcTrigger == null) {
      gcTrigger = defaultGcTrigger();
    }
    
    public interface GcTrigger {
  GcTrigger DEFAULT = new GcTrigger() {
    @Override public void runGc() {
      // Code taken from AOSP FinalizationTest:
      // https://android.googlesource.com/platform/libcore/+/master/support/src/test/java/libcore/
      // java/lang/ref/FinalizationTester.java
      // System.gc() does not garbage collect every time. Runtime.gc() is
      // more likely to perfom a gc.
      //这里用的是Runtime.getRuntime().gc()
      //注意这里和System.gc()的区别
      Runtime.getRuntime().gc();
      //等待100毫秒
      enqueueReferences();
      System.runFinalization();
    }

    private void enqueueReferences() {
      // Hack. We don't have a programmatic way to wait for the reference queue daemon to move
      // references to the appropriate queues.
      try {
        Thread.sleep(100);
      } catch (InterruptedException e) {
        throw new AssertionError();
      }
    }
  };

  void runGc();
}
```
接下来算是`LeakCanary`的一个比较特殊的地方，接下来看到，设置了一个和GC相关的一个类，最终我们会发现是使用的上面放的`DEFAULT`,这里可以看到一个很特殊的一点，这里使用了一个方法`Runtime.getRuntime().gc()`，而且也看到了官方对于此处的注释**这里引用了AOSP的一段代码，System.gc()并不会每次都真正调用回收，所以使用Runtime.getRuntime().gc();**这里就是我们平常不会注意到的知识点，这里需要我们区分一下两个的区别，我自己看了一下两个的源码，并没有发现两个内部的不同（不知道是不是我看的方式的问题），我通过查询，网上对于这两个方法的区别总体是这样解释的。
```
/**
 * Indicates to the VM that it would be a good time to run the
 * garbage collector. Note that this is a hint only. There is no guarantee
 * that the garbage collector will actually be run.
 */
public static void gc() {
    boolean shouldRunGC;
    synchronized(lock) {
        shouldRunGC = justRanFinalization;
        if (shouldRunGC) {
            justRanFinalization = false;
        } else {
            runGC = true;
        }
    }
    if (shouldRunGC) {
        Runtime.getRuntime().gc();
    }
}
```
以上是引用[一篇不错的LeakCanary的源码分析](http://wingjay.com/2017/05/14/dig_into_leakcanary/)中关于gc()源码（不知道为什么我自己看不到这样的源码，如果有人知道，评论告诉我一下，谢谢～～），从这里就可以看出，`System.gc()`的实质其实是调用`Runtime.getRuntime().gc()`，只不过做了一些多线程同步的判断，所以，我们调用`System.gc()`并不会一定出发JVM的GC操作。
到此`build()`方法到这里就分析完了，通过上面的分析我们会发现，到目前为止基本上都是做的准备工作，接下来就是`LeakCanary`的核心操作，检测内存泄漏。

```
//开启LeakCanary的Activity,使图标显示
LeakCanary.enableDisplayLeakActivity(context);

  public static void enableDisplayLeakActivity(Context context) {
    setEnabled(context, DisplayLeakActivity.class, true);
  }
  
  public static void setEnabled(Context context, final Class<?> componentClass,
      final boolean enabled) {
    final Context appContext = context.getApplicationContext();
    executeOnFileIoThread(new Runnable() {
      @Override public void run() {
        setEnabledBlocking(appContext, componentClass, enabled);
      }
    });
  }
  
   public static void setEnabledBlocking(Context appContext, Class<?> componentClass,
      boolean enabled) {
    ComponentName component = new ComponentName(appContext, componentClass);
    PackageManager packageManager = appContext.getPackageManager();
    int newState = enabled ? COMPONENT_ENABLED_STATE_ENABLED : COMPONENT_ENABLED_STATE_DISABLED;
    // Blocks on IPC.
    packageManager.setComponentEnabledSetting(component, newState, DONT_KILL_APP);
  }
```
下面这行代码其实作用是开启LeakCanary的应用图标，使其显示。我们可以看到，这里传入了`DisplayLeakActivity.class `类，最后通过`packageManager.setComponentEnabledSetting`这个方法，将Activity设置为`COMPONENT_ENABLED_STATE_ENABLED `状态。这样设置有什么作用哪，我们来看一下AndroidManifest.xml文件。
```
<activity
        android:theme="@style/leak_canary_LeakCanary.Base"
        android:name=".internal.DisplayLeakActivity"
        android:process=":leakcanary"
        android:enabled="false"
        android:label="@string/leak_canary_display_activity_label"
        android:icon="@mipmap/leak_canary_icon"
        android:taskAffinity="com.squareup.leakcanary.${applicationId}"
        >
      <intent-filter>
        <action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
      </intent-filter>
    </activity>
```
可以看到，这里在清单文件中，将`DisplayLeakActivity `的`enabled`。这里还有一个需要我们注意到点，这里使用了**线程池**。
```
private static final Executor fileIoExecutor = newSingleThreadExecutor("File-IO");

public static void executeOnFileIoThread(Runnable runnable) {
    fileIoExecutor.execute(runnable);
  }
  
  public static Executor newSingleThreadExecutor(String threadName) {
    return Executors.newSingleThreadExecutor(new LeakCanarySingleThreadFactory(threadName));
  }
```
可以看到这里创建了Java中的`newSingleThreadExecutor`线程池，具体特点这里就不详细介绍了，简单的说就是一个唯一的线程，顺序的执行任务。
#### 监听生命周期
```
//默认为true
      if (watchActivities) {
        //注意，在这里通过监听Application,监听Activity的生命周期
        ActivityRefWatcher.install((Application) context, refWatcher);
      }
```
前面的一系列分析，这里终于可以开始监听生命周期，也就是检测内存泄漏的地方了。
```
public static void install(Application application, RefWatcher refWatcher) {
    new ActivityRefWatcher(application, refWatcher).watchActivities();
  }
  
  public void watchActivities() {
    // Make sure you don't get installed twice.
    stopWatchingActivities();
    //注册监听回调
    application.registerActivityLifecycleCallbacks(lifecycleCallbacks);
  }

  public void stopWatchingActivities() {
    application.unregisterActivityLifecycleCallbacks(lifecycleCallbacks);
  }
```
可以看到这里避免重复监听，因为内部是使用一个`ArrayList`进行保存`lifecycleCallbacks `,所以为了和之前的单例保持一致，这里就做移除操作。这里其实我们就要关注，这里是如果实现监听的。
```
private final Application.ActivityLifecycleCallbacks lifecycleCallbacks =
      new Application.ActivityLifecycleCallbacks() {
        @Override public void onActivityCreated(Activity activity, Bundle savedInstanceState) {
        }

        @Override public void onActivityStarted(Activity activity) {
        }

        @Override public void onActivityResumed(Activity activity) {
        }

        @Override public void onActivityPaused(Activity activity) {
        }

        @Override public void onActivityStopped(Activity activity) {
        }

        @Override public void onActivitySaveInstanceState(Activity activity, Bundle outState) {
        }

        @Override public void onActivityDestroyed(Activity activity) {
            //onDestroy的时候回调
          ActivityRefWatcher.this.onActivityDestroyed(activity);
        }
      };
```
可以看到这里利用了Android中的`Application`的特性，注册了`Application.ActivityLifecycleCallbacks`监听器，在Activity的`onDestroy`方法中，调用了`ActivityRefWatcher.this.onActivityDestroyed(activity);`方法。
```
void onActivityDestroyed(Activity activity) {
      //Activity在onDestroy的时候回调
    refWatcher.watch(activity);
  }
```
这里就调用了我们之前构建的`refWatcher`对象的`watch`方法。
```
public void watch(Object watchedReference, String referenceName) {
    if (this == DISABLED) {
      return;
    }
    checkNotNull(watchedReference, "watchedReference");
    checkNotNull(referenceName, "referenceName");
    //获得当前时间
    final long watchStartNanoTime = System.nanoTime();
    //生成一个唯一的key
    String key = UUID.randomUUID().toString();
    //保存这个key
    retainedKeys.add(key);
    //将检查内存泄漏的对象保存为一个弱引用，注意queue
    final KeyedWeakReference reference =
        new KeyedWeakReference(watchedReference, key, referenceName, queue);
    //异步开始分析这个弱引用
    ensureGoneAsync(watchStartNanoTime, reference);
  }
```
这里可以看到，这里使用了当前时间作为唯一标示，这里获取时间的方法也很**讲究**，`System.nanoTime()`这个和`System.currentTimeMillis()`的区别也很简答，这里引用别人的分析简单的说明一下：

>平时产生随机数时我们经常拿时间做种子，比如用System.currentTimeMillis的结果，但是在执行一些循环中使用了System.currentTimeMillis，那么每次的结果将会差别很小，甚至一样，因为现代的计算机运行速度很快。后来看到java中产生随机数函数以及线程池中的一些函数使用的都是System.nanoTime，下面说一下这2个方法的具体区别。
>System.nanoTime提供相对精确的计时，但是不能用他来计算当前日期
[System.nanoTime与System.currentTimeMillis的区别](https://blog.csdn.net/dliyuedong/article/details/8806868)

接下来利用`UUID.randomUUID().toString()`生成了一个唯一的`key`保存在`retainedKeys`集合中，而这个`retainedKeys`是一个`Set`数据类型。
```
// 用于判断弱引用所持有的对象是否已被GC,如果被回收，会存在队列中，反之，没有存在队列中则泄漏了
  private final ReferenceQueue<Object> queue;
final KeyedWeakReference reference =
        new KeyedWeakReference(watchedReference, key, referenceName, queue);

final class KeyedWeakReference extends WeakReference<Object> {
  public final String key;
  public final String name;

  KeyedWeakReference(Object referent, String key, String name,
      ReferenceQueue<Object> referenceQueue) {
    super(checkNotNull(referent, "referent"), checkNotNull(referenceQueue, "referenceQueue"));
    this.key = checkNotNull(key, "key");
    this.name = checkNotNull(name, "name");
  }
}
```
下面这个就是重点了，可以说是`LeakCanary`的核心，可以看到这里new了一个`KeyedWeakReference `对象，这里传入了我们观察的对象，也就是`Activity`,传入了一个`queue`,而这个`queue`可以看到是一个`ReferenceQueue`。而这里`KeyedWeakReference `继承了`WeakReference`，也就是我们熟知的弱引用，熟悉弱引用特性的应该都知道，**当弱引用被回收的时候，会被放入一个队列里**，这里就是利用这个特性，使用**弱引用持有一个Activity对象**。

```
private void ensureGoneAsync(final long watchStartNanoTime, final KeyedWeakReference reference) {
    watchExecutor.execute(new Retryable() {
      @Override public Retryable.Result run() {
        return ensureGone(reference, watchStartNanoTime);
      }
    });
  }
```
接下来就开始了真正开始分析的过程了，可以看到这里使用了我们前面创建的`HandlerThread`这个异步线程进行操作。
```
  // 避免因为gc不及时带来的误判，leakcanay会手动进行gc,进行二次确认进行保证
  Retryable.Result ensureGone(final KeyedWeakReference reference, final long watchStartNanoTime) {
    //System.currentTimeMillis，那么每次的结果将会差别很小，甚至一样，因为现代的计算机运行速度很快
    //检测系统的耗时所用，所以使用System.nanoTime提供相对精确的计时
    long gcStartNanoTime = System.nanoTime();
    long watchDurationMs = NANOSECONDS.toMillis(gcStartNanoTime - watchStartNanoTime);
    //第一次判断，移除此时已经被回收的对象
    removeWeaklyReachableReferences();
    //调试的的时候是否开启内存泄漏判断，默认是false
    if (debuggerControl.isDebuggerAttached()) {
      // The debugger can create false leaks.
      return RETRY;
    }
    //如果此时该对象已经不再retainedKeys中说明第一次判断时该对象已经被回收，不存在内存泄漏
    if (gone(reference)) {
      return DONE;
    }
    //如果当前检测对象还没有被回收，则手动调用gc
    gcTrigger.runGc();
    //再次做一次判断，移除被回收的对象
    removeWeaklyReachableReferences();
    if (!gone(reference)) {
      //如果该对象仍然在retainedKey中，则说明内存泄漏了，进行分析
      long startDumpHeap = System.nanoTime();
      long gcDurationMs = NANOSECONDS.toMillis(startDumpHeap - gcStartNanoTime);
      // dump出来heap，此时认为内存确实已经泄漏了
      File heapDumpFile = heapDumper.dumpHeap();
      if (heapDumpFile == RETRY_LATER) {
        // Could not dump the heap.
        return RETRY;
      }
      long heapDumpDurationMs = NANOSECONDS.toMillis(System.nanoTime() - startDumpHeap);
      //开始分析
      heapdumpListener.analyze(
          new HeapDump(heapDumpFile, reference.key, reference.name, excludedRefs, watchDurationMs,
              gcDurationMs, heapDumpDurationMs));
    }
    return DONE;
  }
```
这里最先看到了`removeWeaklyReachableReferences `这个方法，也就是在`Activity`执行了onDestroy之后，执行这个方法，**进行第一次判断**
```
private void removeWeaklyReachableReferences() {
    // WeakReferences are enqueued as soon as the object to which they point to becomes weakly
    // reachable. This is before finalization or garbage collection has actually happened.
    KeyedWeakReference ref;
    //如果此时已经在queue中，说明已经被回收
    while ((ref = (KeyedWeakReference) queue.poll()) != null) {
      //则从retainedKeys中移除
      retainedKeys.remove(ref.key);
    }
  }
```
这里可以看到，遍历了刚才传入了的弱应用队列，如果弱引用队列中存在引用，说明改对象已经被回收，然后通过存储的唯一性`key`,从`retainedKeys`中移除。
```
//如果此时该对象已经不再retainedKeys中说明第一次判断时该对象已经被回收，不存在内存泄漏
    if (gone(reference)) {
      return DONE;
    }
    private boolean gone(KeyedWeakReference reference) {
    //retainedKeys不存在该对象的key
    return !retainedKeys.contains(reference.key);
  }
```
执行完第一次判断后，这里就判断`retainedKeys `中是否存在该对象的`key`，如果不存在，说明该对象已经成功被GC回收，则表明这时是不存在内存泄漏的，则直接`return`.
```
//如果当前检测对象还没有被回收，则手动调用gc
    gcTrigger.runGc();
    //再次做一次判断，移除被回收的对象
    removeWeaklyReachableReferences();
    if (!gone(reference)) {
      ...
    }
    
    
    GcTrigger DEFAULT = new GcTrigger() {
    @Override public void runGc() {
      // Code taken from AOSP FinalizationTest:
      // https://android.googlesource.com/platform/libcore/+/master/support/src/test/java/libcore/
      // java/lang/ref/FinalizationTester.java
      // System.gc() does not garbage collect every time. Runtime.gc() is
      // more likely to perfom a gc.
      //这里用的是Runtime.getRuntime().gc()
      //注意这里和System.gc()的区别
      Runtime.getRuntime().gc();
      //等待100毫秒
      enqueueReferences();
      System.runFinalization();
    }
    。。。
  };
```
如果这时还存在`retainedKeys `说明**可能存在内存泄漏**，熟悉GC的应该都知道，GC的操作并不是**实时**的，所以第一次虽然该对象还没有被回收，也可能是由于GC没有触发导致的，所以可以看到这里**手动触发了GC操作**，这里就要联系到我们前面分析的`Runtime.getRuntime().gc()`。这样就通了，这里手动调用了`Runtime.getRuntime().gc()`方法，**强制触发GC**。然后在执行一次`removeWeaklyReachableReferences();`方法。再重复做一次判断，弱引用是否被回收，存在于引用队列中。
```
if (!gone(reference)) {
      //如果该对象仍然在retainedKey中，则说明内存泄漏了，进行分析
      long startDumpHeap = System.nanoTime();
      long gcDurationMs = NANOSECONDS.toMillis(startDumpHeap - gcStartNanoTime);
      // dump出来heap，此时认为内存确实已经泄漏了
      File heapDumpFile = heapDumper.dumpHeap();
      if (heapDumpFile == RETRY_LATER) {
        // Could not dump the heap.
        return RETRY;
      }
      long heapDumpDurationMs = NANOSECONDS.toMillis(System.nanoTime() - startDumpHeap);
      //开始分析
      heapdumpListener.analyze(
          new HeapDump(heapDumpFile, reference.key, reference.name, excludedRefs, watchDurationMs,
              gcDurationMs, heapDumpDurationMs));
    }
```
可以看到，当强制GC后，进行第二次判断后，还是存在`retainedKey `中，这里就认为产生了内存泄漏，这时候就开始进行分析，这里就利用了`LeakCanary`使用到的另一个库`Haha`库，用于分析引用路径。首先这里的`heapdumpListener`的实现类就是我们前面提到的`ServiceHeapDumpListener`。
```
@Override protected HeapDump.Listener defaultHeapDumpListener() {
    return new ServiceHeapDumpListener(context, DisplayLeakService.class);
  }
  
  @Override public void analyze(HeapDump heapDump) {
    checkNotNull(heapDump, "heapDump");
    //开启HeapAnalyzerService，是一个HandlerService
    HeapAnalyzerService.runAnalysis(context, heapDump, listenerServiceClass);
  }
  
  public static void  runAnalysis(Context context, HeapDump heapDump,
      Class<? extends AbstractAnalysisResultService> listenerServiceClass) {
    //开启一个IntentService用于分析内存泄漏
    Intent intent = new Intent(context, HeapAnalyzerService.class);
    //将回调的监听Service的class传入，分析完成，回调到这个service
    intent.putExtra(LISTENER_CLASS_EXTRA, listenerServiceClass.getName());
    //收集的文件
    intent.putExtra(HEAPDUMP_EXTRA, heapDump);
    context.startService(intent);
  }
```
这里我们就注意几个关键点就行：
>1. 默认创建的是`ServiceHeapDumpListener `,传入了`DisplayLeakService.class `类对象。
>2. 执行`analyze `方法的实质就是开启`HeapAnalyzerService`这个`Service`,并且将收集的`heapDump `传入用于分析。

```
@Override protected void onHandleIntent(Intent intent) {
    if (intent == null) {
      CanaryLog.d("HeapAnalyzerService received a null intent, ignoring.");
      return;
    }
    String listenerClassName = intent.getStringExtra(LISTENER_CLASS_EXTRA);
    HeapDump heapDump = (HeapDump) intent.getSerializableExtra(HEAPDUMP_EXTRA);

    HeapAnalyzer heapAnalyzer = new HeapAnalyzer(heapDump.excludedRefs);
    //分析获得结果,haha库就在内部调用的，注意分析
    AnalysisResult result = heapAnalyzer.checkForLeak(heapDump.heapDumpFile, heapDump.referenceKey);
    //回调结果
    AbstractAnalysisResultService.sendResultToListener(this, listenerClassName, heapDump, result);
  }
```
这时我们看一下`HeapAnalyzerService`的onHandleIntent方法，这里我们需要注意的就是`heapAnalyzer.checkForLeak`,这个方法就是LeakCanary内部分析引用路径的方法，内部使用了`Haha`库，当然这个过程在一个`IntentService`中，当然是异步的。
```
public static void sendResultToListener(Context context, String listenerServiceClassName,
      HeapDump heapDump, AnalysisResult result) {
    Class<?> listenerServiceClass;
    try {
      listenerServiceClass = Class.forName(listenerServiceClassName);
    } catch (ClassNotFoundException e) {
      throw new RuntimeException(e);
    }
    //启动Service通知，抽象类，DisplayLeakService
    Intent intent = new Intent(context, listenerServiceClass);
    //将分析的信息传回给Service,发出内存泄漏的通知
    intent.putExtra(HEAP_DUMP_EXTRA, heapDump);
    intent.putExtra(RESULT_EXTRA, result);
    context.startService(intent);
  }
```
当分析完结果后，可以看到这里，利用**反射**，创建了我们之前传入的`DisplayLeakService `对象，然后将分析接口发送给`DisplayLeakService `。
```
@Override protected final void onHeapAnalyzed(HeapDump heapDump, AnalysisResult result) {
    String leakInfo = leakInfo(this, heapDump, result, true);
    CanaryLog.d("%s", leakInfo);

    boolean resultSaved = false;
    boolean shouldSaveResult = result.leakFound || result.failure != null;
    if (shouldSaveResult) {
      heapDump = renameHeapdump(heapDump);
      resultSaved = saveResult(heapDump, result);
    }

    PendingIntent pendingIntent;
    String contentTitle;
    String contentText;

    if (!shouldSaveResult) {
      //无泄露
      contentTitle = getString(R.string.leak_canary_no_leak_title);
      contentText = getString(R.string.leak_canary_no_leak_text);
      pendingIntent = null;
    } else if (resultSaved) {
      //获得一个pendingIntent
      pendingIntent = DisplayLeakActivity.createPendingIntent(this, heapDump.referenceKey);

      if (result.failure == null) {
        String size = formatShortFileSize(this, result.retainedHeapSize);
        String className = classSimpleName(result.className);
        if (result.excludedLeak) {
          contentTitle = getString(R.string.leak_canary_leak_excluded, className, size);
        } else {
          contentTitle = getString(R.string.leak_canary_class_has_leaked, className, size);
        }
      } else {
        contentTitle = getString(R.string.leak_canary_analysis_failed);
      }
      contentText = getString(R.string.leak_canary_notification_message);
    } else {
      contentTitle = getString(R.string.leak_canary_could_not_save_title);
      contentText = getString(R.string.leak_canary_could_not_save_text);
      pendingIntent = null;
    }
    // New notification id every second.
    int notificationId = (int) (SystemClock.uptimeMillis() / 1000);
    //显示一个通知，显示内存泄漏
    showNotification(this, contentTitle, contentText, pendingIntent, notificationId);
    afterDefaultHandling(heapDump, result, leakInfo);
  }
```
这里由于`DisplayLeakService`继承了`AbstractAnalysisResultService`,而`AbstractAnalysisResultService`继承了`IntentService`，最终会调`onHeapAnalyzed `方法，这里可以看到当存在内存泄漏的时候，会创建一个`pendingIntent `用于后面通知的点击事件跳转，而后发送了一个通知`notification `。

#### `LeakCanary.isInAnalyzerProcess(context);`
这里我们再来看一下前面提到的`LeakCanary`提供给我们的一个比较不错的工具类，用于判断当前进程是否在后台。
```
public static boolean isInAnalyzerProcess(Context context) {
    Boolean isInAnalyzerProcess = LeakCanaryInternals.isInAnalyzerProcess;
    // This only needs to be computed once per process.
    if (isInAnalyzerProcess == null) {
      //判断进程是否在后台，重要
      isInAnalyzerProcess = isInServiceProcess(context, HeapAnalyzerService.class);
      LeakCanaryInternals.isInAnalyzerProcess = isInAnalyzerProcess;
    }
    return isInAnalyzerProcess;
  }
  
  public static boolean isInServiceProcess(Context context, Class<? extends Service> serviceClass) {
    PackageManager packageManager = context.getPackageManager();
    PackageInfo packageInfo;
    try {
      packageInfo = packageManager.getPackageInfo(context.getPackageName(), GET_SERVICES);
    } catch (Exception e) {
      CanaryLog.d(e, "Could not get package info for %s", context.getPackageName());
      return false;
    }
    String mainProcess = packageInfo.applicationInfo.processName;

    ComponentName component = new ComponentName(context, serviceClass);
    ServiceInfo serviceInfo;
    try {
      serviceInfo = packageManager.getServiceInfo(component, 0);
    } catch (PackageManager.NameNotFoundException ignored) {
      // Service is disabled.
      return false;
    }

    if (serviceInfo.processName.equals(mainProcess)) {
      //如果服务进程和主进程是同一个进程，那就不对了
      CanaryLog.d("Did not expect service %s to run in main process %s", serviceClass, mainProcess);
      // Technically we are in the service process, but we're not in the service dedicated process.
      return false;
    }

    int myPid = android.os.Process.myPid();
    ActivityManager activityManager =
        (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
    ActivityManager.RunningAppProcessInfo myProcess = null;
    List<ActivityManager.RunningAppProcessInfo> runningProcesses;
    try {
      runningProcesses = activityManager.getRunningAppProcesses();
    } catch (SecurityException exception) {
      // https://github.com/square/leakcanary/issues/948
      CanaryLog.d("Could not get running app processes %d", exception);
      return false;
    }
    if (runningProcesses != null) {
      for (ActivityManager.RunningAppProcessInfo process : runningProcesses) {
        //获取当前正在前台对进程
        if (process.pid == myPid) {
          myProcess = process;
          break;
        }
      }
    }
    if (myProcess == null) {
      CanaryLog.d("Could not find running process for %d", myPid);
      return false;
    }

    return myProcess.processName.equals(serviceInfo.processName);
  }
```
思路还是比较清晰的，遍历当前的所有运行中的进程，获得当前运行的主进程，然后和对应的进程名称做对比。
### 总结
到此LeakCanary的整个流程已经走完了，可能写的比较琐碎，但是大体流程还是比较清晰的。
>1.通过Application监听Activity的生命周期
>2.在Activity的Destroy时，进行内存泄漏分析。
>3.利用弱应用的特性使用一个引用队列保存Activity的引用，如果onDestroy后引用队列中存在该Activity的实例则说明成功回收。
>4.若不存在，则手动利用Runtime.getRuntime().gc()方法手动触发GC，执行完后再进行一次判断。
>5.若此时还没有在队列中存在，说明没有被回收，则认定此时发生内存泄漏。
>6.异步执行Haha库进行引用链分析，然后通知Service发出通知。
