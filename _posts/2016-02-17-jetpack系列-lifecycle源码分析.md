---
title: "【JetPack系列】——Lifecycle源码分析"
date: 2020-06-14 22:18:37+08:00
categories: ["Android源码分析"]
source_name: "【JetPack系列】——Lifecycle源码分析"
jianshu_views: 1255
jianshu_url: "https://www.jianshu.com/p/175a2138f5e2"
---
>本系列博客基于androidx-2.2.0版本
[【JetPack系列】——Lifecycle源码分析](https://www.jianshu.com/p/175a2138f5e2)
[【JetPack系列】——LiveData源码解析](https://www.jianshu.com/p/b047bcfb2a04)
[【JetPack系列】——ViewModel源码解析](https://www.jianshu.com/p/1715d7826191)
### 前言
Google的JetPack组件已经出了一段时间了，正如Google说明的那样，利用这套框架可以很便捷的帮助开发者快速的迭代开发，这应该是Google官方推出的较为正规的一套框架了，无论从设计还是目前的应用推广程度，都是目前Android开发者需要掌握的一套框架。本系列主要分析JetPack的三个框架：`Lifecycle`、`LiveData`、`ViewModel`。  
本篇博客主要分析我认为是三个组件的根基`Lifecycle`,正是`Lifecycle`的出现，为后面的很多框架提供了感知生命周期的基础能力。  
首先对于`Lifecycle`我们应该有一个基础的认知，这个框架是干什么的。这里放上Google官方介绍的地[地址](https://developer.android.com/topic/libraries/architecture/lifecycle)。简单的说`Lifecycle`是一个用于赋予组件感知生命周期能力的框架，看到这里我们对于这个框架的第一个想法应该是**观察者者模式**，没错，因为无论框架用到了什么高大上的技术，最基础的原理肯定是感知`Activity`的生命周期，然后通过注册观察者分发下去，至于里面用到了一些看似高科技的技术，只是一个框架从设计角度来简便使用者的使用成本，所以至此，我们第一步先对`Lifecycle`有了一个基础的认知。
### 源码分析
既然前面提到了观察者模式，那么我们阅读源码的思路就很清晰了，我们这里分为两个部分：1.观察者2.被观察者。
#### 被观察者-LifecycleOwner
```
public interface LifecycleOwner {
    Lifecycle getLifecycle();
}
```
我们来看下被观察者的接口，很简单，没有过多复杂的方法，那么既然是被观察者，能体现生命周期的肯定脱离不了`Activity`、`Fragment`这两者，所以我们看下这个接口的实现类，果然找到了和`Activity`相关的身影-`SupportActivity`
```
public class SupportActivity extends Activity implements LifecycleOwner {
    private SimpleArrayMap<Class<? extends SupportActivity.ExtraData>, SupportActivity.ExtraData> mExtraDataMap = new SimpleArrayMap();
    private LifecycleRegistry mLifecycleRegistry = new LifecycleRegistry(this);

    public SupportActivity() {
    }

    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        ReportFragment.injectIfNeededIn(this);
    }

    public Lifecycle getLifecycle() {
        return this.mLifecycleRegistry;
    }
}
```
这里简化了下代码，可以看到两个核心的地方，一个是重写了`getLifecycle()`方法，可以看到`Lifecycle`的实现类`LifecycleRegistry`，一个是`ReportFragment.injectIfNeededIn(this);`
```
public static void injectIfNeededIn(Activity activity) {
        FragmentManager manager = activity.getFragmentManager();
        if(manager.findFragmentByTag("android.arch.lifecycle.LifecycleDispatcher.report_fragment_tag") == null) {
            manager.beginTransaction().add(new ReportFragment(), "android.arch.lifecycle.LifecycleDispatcher.report_fragment_tag").commit();
            manager.executePendingTransactions();
        }

    }
```
首先看下`injectIfNeededIn`方法，这里可以看到这个方法就是一个向`Activity`注入`Fragment`的方法，看到这里如果我们看过`Glide`的源码或者了解过`Glide`的原理的，我们应该会联想到这里的`Fragment`的作用会不会是一个空的`Fragment`用于感知生命周期的。
```
public class ReportFragment extends Fragment {
    private static final String REPORT_FRAGMENT_TAG = "android.arch.lifecycle.LifecycleDispatcher.report_fragment_tag";
    private ReportFragment.ActivityInitializationListener mProcessListener;

    public ReportFragment() {
    }

    static ReportFragment get(Activity activity) {
        return (ReportFragment)activity.getFragmentManager().findFragmentByTag("android.arch.lifecycle.LifecycleDispatcher.report_fragment_tag");
    }

    private void dispatchCreate(ReportFragment.ActivityInitializationListener listener) {
        if(listener != null) {
            listener.onCreate();
        }

    }

    private void dispatchStart(ReportFragment.ActivityInitializationListener listener) {
        if(listener != null) {
            listener.onStart();
        }

    }

    private void dispatchResume(ReportFragment.ActivityInitializationListener listener) {
        if(listener != null) {
            listener.onResume();
        }

    }

    public void onActivityCreated(Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);
        this.dispatchCreate(this.mProcessListener);
        this.dispatch(Event.ON_CREATE);
    }

    public void onStart() {
        super.onStart();
        this.dispatchStart(this.mProcessListener);
        this.dispatch(Event.ON_START);
    }

    public void onResume() {
        super.onResume();
        this.dispatchResume(this.mProcessListener);
        this.dispatch(Event.ON_RESUME);
    }

    public void onPause() {
        super.onPause();
        this.dispatch(Event.ON_PAUSE);
    }

    public void onStop() {
        super.onStop();
        this.dispatch(Event.ON_STOP);
    }

    public void onDestroy() {
        super.onDestroy();
        this.dispatch(Event.ON_DESTROY);
        this.mProcessListener = null;
    }

    private void dispatch(Event event) {
        Activity activity = this.getActivity();
        if(activity instanceof LifecycleRegistryOwner) {
            ((LifecycleRegistryOwner)activity).getLifecycle().handleLifecycleEvent(event);
        } else {
            if(activity instanceof LifecycleOwner) {
                Lifecycle lifecycle = ((LifecycleOwner)activity).getLifecycle();
                if(lifecycle instanceof LifecycleRegistry) {
                    ((LifecycleRegistry)lifecycle).handleLifecycleEvent(event);
                }
            }

        }
    }

    void setProcessListener(ReportFragment.ActivityInitializationListener processListener) {
        this.mProcessListener = processListener;
    }

    interface ActivityInitializationListener {
        void onCreate();

        void onStart();

        void onResume();
    }
}
```
这里放上了源码，果然和我们想的一样，这里其实就是一个空的`Fragment`，用于感知生命周期，然后子在`dispatch`方法里分发，因为`LifecycleRegistryOwner`已经是一个**过时**的类了，所以这里就不做分析，刚才我们也看到了我们的`SupportActivity`是实现了`LifecycleOwner`接口，所以这里可以看到就会调用`LifecycleRegistry`的`handlerLifecycleEvent`方法。
所以这里我们可以得出一个结论：**被观察者通过注入一个空的Fragment来感知生命周期并分发**
但我们这里可能会有一个疑问，如果我们没有继承这个`SupportActivity`怎么办。我们可以看下调用`injectIfNeededIn`方法的地方，会发现除了`SupportActivity`还会有一个地方调用`LifecycleDispatcher`
```
class LifecycleDispatcher {

    private static AtomicBoolean sInitialized = new AtomicBoolean(false);

    static void init(Context context) {
        if (sInitialized.getAndSet(true)) {
            return;
        }
        ((Application) context.getApplicationContext())
                .registerActivityLifecycleCallbacks(new DispatcherActivityCallback());
    }

    @SuppressWarnings("WeakerAccess")
    @VisibleForTesting
    static class DispatcherActivityCallback extends EmptyActivityLifecycleCallbacks {

        @Override
        public void onActivityCreated(Activity activity, Bundle savedInstanceState) {
            ReportFragment.injectIfNeededIn(activity);
        }

        @Override
        public void onActivityStopped(Activity activity) {
        }

        @Override
        public void onActivitySaveInstanceState(Activity activity, Bundle outState) {
        }
    }

    private LifecycleDispatcher() {
    }
}

```
这样就比较清晰了，可以看到其实通过`Application`的`registerActivityLifecycleCallbacks`方法，来向`Activity`中注入`Fragment`。这里有个比较奇妙的地方，可以看下调用`init`方法的地方。
```
public class ProcessLifecycleOwnerInitializer extends ContentProvider {
    @Override
    public boolean onCreate() {
        LifecycleDispatcher.init(getContext());
        ProcessLifecycleOwner.init(getContext());
        return true;
    }
}
```
会发现，Google其实用一个`ContentProvider`来实习**无痕初始化**这里特意提下`ContentProvider`的特性，我们只需要在`AndroidManifest.xml`文件中配置一下`ContentProvider`的信息，就不需要在`Application`或其他地方做初始化的操作，`ContentProvider`会在`Application`初始化前自动就加载进来，具体就不在这里展开说明了。（其实LeakCanary2也是利用这个特性来完成的**无痕初始化**）
### 观察者-LifecycleObserver
```
public interface LifecycleObserver {

}
```
可以看到观察者其实是一个空接口，但其实有很多对应的实现接口例如：
```
interface FullLifecycleObserver extends LifecycleObserver {

    void onCreate(LifecycleOwner owner);

    void onStart(LifecycleOwner owner);

    void onResume(LifecycleOwner owner);

    void onPause(LifecycleOwner owner);

    void onStop(LifecycleOwner owner);

    void onDestroy(LifecycleOwner owner);
}

public interface LifecycleEventObserver extends LifecycleObserver {
    /**
     * Called when a state transition event happens.
     *
     * @param source The source of the event
     * @param event The event
     */
    void onStateChanged(@NonNull LifecycleOwner source, @NonNull Lifecycle.Event event);
}
```
也就是我们可以实现不同的接口，来实现我们感应生命周期的需求。
>但其实我对于这的设计是感觉有一些不妥的，Google在这里提供了丰富的接口，来对应我们使用不同的需求，但是这也给这套框架本身带来了很大的不便，后面的分析可以看到Lifecycle需要对应每一个接口做一个adapter适配，最终适配为一种类型，这个无疑增加了开发成本和理解成本，并且从设计来说，以一个空接口作为判断的依据，我认为是有一些不妥的，虽然对于使用者的出发点是好的，但是也一方面增加了使用者的学习成本，
#### 注册观察者-addObserver
```
public void addObserver(LifecycleObserver observer) {
        State initialState = this.mState == State.DESTROYED?State.DESTROYED:State.INITIALIZED;
		//1.包装适配不同的接口类型
        LifecycleRegistry.ObserverWithState statefulObserver = new LifecycleRegistry.ObserverWithState(observer, initialState);
		//2.增加观察者
        LifecycleRegistry.ObserverWithState previous = (LifecycleRegistry.ObserverWithState)this.mObserverMap.putIfAbsent(observer, statefulObserver);
        if(previous == null) {
            boolean isReentrance = this.mAddingObserverCounter != 0 || this.mHandlingEvent;
			//3.粘性事件，保持生命周期一致
            State targetState = this.calculateTargetState(observer);
            ++this.mAddingObserverCounter;

            while(statefulObserver.mState.compareTo(targetState) < 0 && this.mObserverMap.contains(observer)) {
                this.pushParentState(statefulObserver.mState);
                statefulObserver.dispatchEvent(this.mLifecycleOwner, upEvent(statefulObserver.mState));
                this.popParentState();
                targetState = this.calculateTargetState(observer);
            }

            if(!isReentrance) {
			///4.分发
                this.sync();
            }

            --this.mAddingObserverCounter;
        }
    }
```
这个其实是我将观察分为了四个步骤：
* 1.包装适配不同的接口类型
* 2.增加观察者
* 3.粘性事件，保持生命周期的一致
* 4.分发
所以这里我们也分为了四个小块来看一下
##### 包装适配不同的接口类型
```
static class ObserverWithState {
        State mState;
        GenericLifecycleObserver mLifecycleObserver;

        ObserverWithState(LifecycleObserver observer, State initialState) {
			//传入的LifecycleObserver转换成了GenericLifecycleObserver
            this.mLifecycleObserver = Lifecycling.getCallback(observer);
            this.mState = initialState;
        }

        void dispatchEvent(LifecycleOwner owner, Event event) {
            State newState = LifecycleRegistry.getStateAfter(event);
            this.mState = LifecycleRegistry.min(this.mState, newState);
            this.mLifecycleObserver.onStateChanged(owner, event);
            this.mState = newState;
        }
    }
```
这里其实最核心的步骤就是拿`ObserverWithState`将我们传入的`LifecycleObserver`包装起来，转换成`GenericLifecycleObserver`。核心的转化方法就是在`Lifecycling.getCallback(observer);`中。
```
@NonNull
static GenericLifecycleObserver getCallback(Object object) {
	//实现了FullLifecycleObserver接口
    if (object instanceof FullLifecycleObserver) {
        return new FullLifecycleObserverAdapter((FullLifecycleObserver) object);
    }
	//实现了GenericLifecycleObserver接口
    if (object instanceof GenericLifecycleObserver) {
        return (GenericLifecycleObserver) object;
    }
	//使用了注解，这里分为编译期注解和运行时注解
    final Class<?> klass = object.getClass();
    int type = getObserverConstructorType(klass);
    // 获取 type
    // GENERATED_CALLBACK 表示注解生成的代码
    // REFLECTIVE_CALLBACK 表示使用反射
    if (type == GENERATED_CALLBACK) {
		//编译期注解
        List<Constructor<? extends GeneratedAdapter>> constructors =
                sClassToAdapters.get(klass);
        if (constructors.size() == 1) {
            GeneratedAdapter generatedAdapter = createGeneratedAdapter(
                    constructors.get(0), object);
            return new SingleGeneratedAdapterObserver(generatedAdapter);
        }
        GeneratedAdapter[] adapters = new GeneratedAdapter[constructors.size()];
        for (int i = 0; i < constructors.size(); i++) {
            adapters[i] = createGeneratedAdapter(constructors.get(i), object);
        }
        return new CompositeGeneratedAdaptersObserver(adapters);
    }
    return new ReflectiveGenericLifecycleObserver(object);
}
```
其实可以看到就是那一个包装类将我们传入的类型转换成了`GenericLifecycleObserver`类型，这里主要看下如何区分编译期注解和运行时注解的，首先说明下两个区别
>1.编译期注解：其实了解AOP的应该都知道现在有很多注解作用于编译期，在编译的过程中，通过识别注解，来插入对应的代码或者生成对应的代码，
>2.运行时注解：其实就是反射，通过反射来找到对应的注解的内容，来执行对应的操作，反射需要注意混淆带来的影响。
```
private static int getObserverConstructorType(Class<?> klass) {
	//这里有一个缓存，增加效率
    if (sCallbackCache.containsKey(klass)) {
        return sCallbackCache.get(klass);
    }
    int type = resolveObserverCallbackType(klass);
    sCallbackCache.put(klass, type);
    return type;
}

private static int resolveObserverCallbackType(Class<?> klass) {
    // anonymous class bug:35073837
    // 匿名内部类使用反射
    if (klass.getCanonicalName() == null) {
        return REFLECTIVE_CALLBACK;
    }

    // 寻找注解生成的 GeneratedAdapter 类
    Constructor<? extends GeneratedAdapter> constructor = generatedConstructor(klass);
    if (constructor != null) {
        sClassToAdapters.put(klass, Collections
                .<Constructor<? extends GeneratedAdapter>>singletonList(constructor));
        return GENERATED_CALLBACK;
    }

    // 寻找被 OnLifecycleEvent 注解的方法
    boolean hasLifecycleMethods = ClassesInfoCache.sInstance.hasLifecycleMethods(klass);
    if (hasLifecycleMethods) {
        return REFLECTIVE_CALLBACK;
    }

    // 没有找到注解生成的 GeneratedAdapter 类，也没有找到 OnLifecycleEvent 注解，
    // 则向上寻找父类
    Class<?> superclass = klass.getSuperclass();
    List<Constructor<? extends GeneratedAdapter>> adapterConstructors = null;
    if (isLifecycleParent(superclass)) {
        if (getObserverConstructorType(superclass) == REFLECTIVE_CALLBACK) {
            return REFLECTIVE_CALLBACK;
        }
        adapterConstructors = new ArrayList<>(sClassToAdapters.get(superclass));
    }

    // 寻找是否有接口实现
    for (Class<?> intrface : klass.getInterfaces()) {
        if (!isLifecycleParent(intrface)) {
            continue;
        }
        if (getObserverConstructorType(intrface) == REFLECTIVE_CALLBACK) {
            return REFLECTIVE_CALLBACK;
        }
        if (adapterConstructors == null) {
            adapterConstructors = new ArrayList<>();
        }
        adapterConstructors.addAll(sClassToAdapters.get(intrface));
    }
    if (adapterConstructors != null) {
        sClassToAdapters.put(klass, adapterConstructors);
        return GENERATED_CALLBACK;
    }

    return REFLECTIVE_CALLBACK;
}
```
这里面的方法就不在这里展开了，单独看一下如何找到编译期的类吧，其他的其实都是反射的常用操作，找父类是否实现，找注解方法，遍历接口的方法，没有复杂的代码。
```
@Nullable
    private static Constructor<? extends GeneratedAdapter> generatedConstructor(Class<?> klass) {
        try {
            Package aPackage = klass.getPackage();
            String name = klass.getCanonicalName();
            final String fullPackage = aPackage != null ? aPackage.getName() : "";
            final String adapterName = getAdapterName(fullPackage.isEmpty() ? name :
                    name.substring(fullPackage.length() + 1));

            @SuppressWarnings("unchecked") final Class<? extends GeneratedAdapter> aClass =
                    (Class<? extends GeneratedAdapter>) Class.forName(
                            fullPackage.isEmpty() ? adapterName : fullPackage + "." + adapterName);
            Constructor<? extends GeneratedAdapter> constructor =
                    aClass.getDeclaredConstructor(klass);
            if (!constructor.isAccessible()) {
                constructor.setAccessible(true);
            }
            return constructor;
        } catch (ClassNotFoundException e) {
            return null;
        } catch (NoSuchMethodException e) {
            // this should not happen
            throw new RuntimeException(e);
        }
    }

 /**
     * Create a name for an adapter class.
     */
    public static String getAdapterName(String className) {
        return className.replace(".", "_") + "_LifecycleAdapter";
    }
```
这里可以看到其实这里也是用反射去找类，并且通过`Class.forName`去加载类，然后通过反射来得到构造函数。这里比较有趣的是这里获取类名的时候，其实是用字符串拼接**LifecycleAdapter**，如果使用过`Lifecycle`的注解的应该会发现，当你使用一个注解后，在编译期通过后，会自动生成一个**xxxx_LifecycleAdapter**类。
```
@Generated("androidx.lifecycle.LifecycleProcessor")
public class ObserverNoAdapter_LifecycleAdapter implements GeneratedAdapter {
    final ObserverNoAdapter mReceiver;

    ObserverNoAdapter_LifecycleAdapter(ObserverNoAdapter receiver) {
        this.mReceiver = receiver;
    }

    @Override
    public void callMethods(LifecycleOwner owner, Lifecycle.Event event, boolean onAny,
            MethodCallsLogger logger) {
        boolean hasLogger = logger != null;
        if (onAny) {
            return;
        }
        if (event == Lifecycle.Event.ON_STOP) {
            if (!hasLogger || logger.approveCall("doOnStop", 1)) {
                mReceiver.doOnStop();
            }
            return;
        }
    }
}

```
可以看懂，其实和上面的类没有太大的区别，只不过就是通过编译期注解来生成的，然后通过`Class.forName`来获取。
至此，我们第一小步已经分析完成了，我们可以总结下：
>1.我们传入的`LifecycleObserver`会被转换成`GenericLifecycleObserver`
>2.转换的方式根据我们的实现方式不同对应不同，其中要注意的是编译期注解是在编译时生成的LifecycleAdapter结尾的包装类
>3.我还是觉得Google这样有点秀操作的意思，维护和学习成本变高了
##### 2.增加观察者
```
	LifecycleRegistry.ObserverWithState previous = (LifecycleRegistry.ObserverWithState)this.mObserverMap.putIfAbsent(observer, statefulObserver);
```
这里看似简单，起初我也是感觉没有什么好分析的，但是有一次，我在使用Map的过程中，循环中使用remove导致ConcurrentModificationException，这个地方引起了我的注意，我们在使用`Lifecycle`的时候，如果在生命周期内移除了`Observer`，是不会出现异常的，这一点就引起了我的兴趣。最后我发现这归功于这里特殊的Map结构，所以我们这里来看一下使用的Map结构吧。
```
/**
 * Poor's man LinkedHashMap, which supports modifications during iterations.
 * Takes more memory that {@link SafeIterableMap}
 * It is NOT thread safe.
 *
 * @param <K> Key type
 * @param <V> Value type
 * @hide
 */
@RestrictTo(RestrictTo.Scope.LIBRARY_GROUP_PREFIX)
public class FastSafeIterableMap<K, V> extends SafeIterableMap<K, V> {

    private HashMap<K, Entry<K, V>> mHashMap = new HashMap<>();

    @Override
    protected Entry<K, V> get(K k) {
        return mHashMap.get(k);
    }

    @Override
    public V putIfAbsent(@NonNull K key, @NonNull V v) {
        Entry<K, V> current = get(key);
        if (current != null) {
            return current.mValue;
        }
        mHashMap.put(key, put(key, v));
        return null;
    }

    @Override
    public V remove(@NonNull K key) {
        V removed = super.remove(key);
        mHashMap.remove(key);
        return removed;
    }

    /**
     * Returns {@code true} if this map contains a mapping for the specified
     * key.
     */
    public boolean contains(K key) {
        return mHashMap.containsKey(key);
    }

    /**
     * Return an entry added to prior to an entry associated with the given key.
     *
     * @param k the key
     */
    public Map.Entry<K, V> ceil(K k) {
        if (contains(k)) {
            return mHashMap.get(k).mPrevious;
        }
        return null;
    }
}
```
这里首先看下名字，就很有意思`FastSafeIterableMap`，直译过来就是**又快又安全**，在看下注释
```
/**
 * Poor's man LinkedHashMap, which supports modifications during iterations.
 * Takes more memory that {@link SafeIterableMap}
 * It is NOT thread safe
 * 低配版的LinkedHashMap，支持循环的时候修改内容，比SafeIterableMap更耗费内存，不是线程安全的。 
 **/
```
所以我们通过注释可以了解到这个是一个支持在循环的时候修改内容的Map，这个其实就很好，而我们在看下到底是如何实现这样的功能，我们看下这个类的父类。
```
public class SafeIterableMap<K, V> implements Iterable<Map.Entry<K, V>> {

    @SuppressWarnings("WeakerAccess") /* synthetic access */
    Entry<K, V> mStart;
    private Entry<K, V> mEnd;
    // using WeakHashMap over List<WeakReference>, so we don't have to manually remove
    // WeakReferences that have null in them.
    private WeakHashMap<SupportRemove<K, V>, Boolean> mIterators = new WeakHashMap<>();
    private int mSize = 0;

    /**
     * Removes the mapping for a key from this map if it is present.
     *
     * @param key key whose mapping is to be removed from the map
     * @return the previous value associated with the specified key,
     * or {@code null} if there was no mapping for the key
     */
    public V remove(@NonNull K key) {
        Entry<K, V> toRemove = get(key);
        if (toRemove == null) {
            return null;
        }
        mSize--;
        if (!mIterators.isEmpty()) {
            for (SupportRemove<K, V> iter : mIterators.keySet()) {
                iter.supportRemove(toRemove);
            }
        }

        if (toRemove.mPrevious != null) {
            toRemove.mPrevious.mNext = toRemove.mNext;
        } else {
            mStart = toRemove.mNext;
        }

        if (toRemove.mNext != null) {
            toRemove.mNext.mPrevious = toRemove.mPrevious;
        } else {
            mEnd = toRemove.mPrevious;
        }

        toRemove.mNext = null;
        toRemove.mPrevious = null;
        return toRemove.mValue;
    }
}
```
具体这里就不全部放出来了，这里自看下核心的关键的地方，可以看到这里其实是一个用一个链表的结构，而我们的remove也会对应的修改链表的指针，在使用游标遍历的时候，也没有做关于`ConcurrentModificationException`的检测，这个Map的实现还是很值得我们学习的，但是这里要吐槽下，为啥Google不把这个类开放出来，这个类其实是一个包私有的类，也是我们平时的开发无法使用的，可能也是考虑性能的因素，而且和正常的数据结构还是有差异的。
##### 粘性事件，保持生命周期一致
```
State targetState = this.calculateTargetState(observer);
            ++this.mAddingObserverCounter;

            while(statefulObserver.mState.compareTo(targetState) < 0 && this.mObserverMap.contains(observer)) {
                this.pushParentState(statefulObserver.mState);
                statefulObserver.dispatchEvent(this.mLifecycleOwner, upEvent(statefulObserver.mState));
                this.popParentState();
                targetState = this.calculateTargetState(observer);
            }
```
这一步我个人感觉其实是`Lifecycle`和`LiveData`的核心思想，这里首先提一问题：
>如果在onResumed的时候注册了Observer，那么我们的Observer的生命周期会如何回调

这里就不得不吹一波Google的设计了，如果交给我们设计一款生命周期感知的组件，我们可能就是基础的观察者模式，然后再对应的生命周期，利用遍历，通知观察者就可以了。但是Google在这里的考虑了两个概念，一个是**倒灌**(我个人比较喜欢称**粘性**)，一个是**重入**，现在说这两个概念可能会让人有点困扰，所以我们先一步一步分析，后面再围绕两个概念展开。
```
private State calculateTargetState(LifecycleObserver observer) {
		//之前的观察者的生命周期
        Entry<LifecycleObserver, LifecycleRegistry.ObserverWithState> previous = this.mObserverMap.ceil(observer);
        State siblingState = previous != null?((LifecycleRegistry.ObserverWithState)previous.getValue()).mState:null;
        State parentState = !this.mParentStates.isEmpty()?(State)
		//和重入概念有关，常规情况为null
		this.mParentStates.get(this.mParentStates.size() - 1):null;
		、、比较当前state和之前的观察者的状态的最小者
        return min(min(this.mState, siblingState), parentState);
    }
```
这里做了三个比较，比较了之前已经加入的观察者的生命周期和当前被观察者的生命周期，parentState的和重入有关系，所以这里暂时先不讨论，后面会分析。这里就拿我们刚才举例的那个例子来分析，我们在Activity的onResume的生命周期里面加入一个Observer，这时`mState`为`STARTED`(因为Activity正在执行onResume所以，state还没有变换)，而我们这个是第一个观察者，所以之前的观察者为空，所以本次计算的`calculateTargetState`为`STARTED`。
```
while(statefulObserver.mState.compareTo(targetState) < 0 && this.mObserverMap.contains(observer)) {
                this.pushParentState(statefulObserver.mState);
                statefulObserver.dispatchEvent(this.mLifecycleOwner, upEvent(statefulObserver.mState));
                this.popParentState();
                targetState = this.calculateTargetState(observer);
            }
```
这时我们新创建的Observer的生命周期为`INITIALIZED`，所以肯定是小于`targetState`,进入`while`循环。这里的State其实就是一个枚举，所以`compareTo`比较的就是枚举的大小。
```
public static enum State {
        DESTROYED,
        INITIALIZED,
        CREATED,
        STARTED,
        RESUMED;

        private State() {
        }

        public boolean isAtLeast(Lifecycle.State state) {
            return this.compareTo(state) >= 0;
        }
    }
```
进入while循环后，会首先把`Observer`加入`mParentStates`(和重入有关，先不考虑)，然后执行`dispatchEvent`，看到这个方法名，其实应该就能感受到，这里其实就是执行分发操作.
```
private static Event upEvent(State state) {
        switch(null.$SwitchMap$android$arch$lifecycle$Lifecycle$State[state.ordinal()]) {
        case 1:
        case 5:
            return Event.ON_CREATE;
        case 2:
            return Event.ON_START;
        case 3:
            return Event.ON_RESUME;
        case 4:
            throw new IllegalArgumentException();
        default:
            throw new IllegalArgumentException("Unexpected state value " + state);
        }
    }

void dispatchEvent(LifecycleOwner owner, Event event) {
            State newState = LifecycleRegistry.getStateAfter(event);
            this.mState = LifecycleRegistry.min(this.mState, newState);
            this.mLifecycleObserver.onStateChanged(owner, event);
            this.mState = newState;
        }
```
可以看到，其实就是按照生命周期的顺序，逐步向后分发。所以我们当前的是`INITIALIZED`，第一次会返回`Event.ON_CREATE`回调给观察者。然后继续执行`calculateTargetState`，按照刚才的逻辑，肯定还是小于当前的生命周期`STARTED`，所以会继续执行while循环分发生命周期，直到观察者的生命周期也是`STARTED`。
这里我们其实就会有一个结论，这个其实有点像消息总线里面的**粘性**，我们在注册观察者的时候，会首选将我们的观察者同步到当前被观察者的生命周期，并且是逐步上升。也就是说我们调用`addObserver`的时候，我们注册的观察者如果和当前被观察者的生命周期有差异，那么我们会收到回调，然后同步生命周期。
#### 分发
```
private void sync() {
        while(!this.isSynced()) {
            this.mNewEventOccurred = false;
            if(this.mState.compareTo(((LifecycleRegistry.ObserverWithState)this.mObserverMap.eldest().getValue()).mState) < 0) {
                this.backwardPass();
            }

            Entry<LifecycleObserver, LifecycleRegistry.ObserverWithState> newest = this.mObserverMap.newest();
            if(!this.mNewEventOccurred && newest != null && this.mState.compareTo(((LifecycleRegistry.ObserverWithState)newest.getValue()).mState) > 0) {
                this.forwardPass();
            }
        }

        this.mNewEventOccurred = false;
    }
```
到观察的最后一步了，这里其实就比较简单了，还是刚才的`compareTo`逻辑，只不过比较的对象变成了我们观察者链表的头和尾，我们刚才已经加入观察者，并且同步到最新的生命周期了，这里会再次比较，保证链表的首尾的生命周期相同。而`backwardPass`和`forwardPass`我这里就不展开了，其实名字就已经很直观的表现了这个方法的作用，就是比较生命周期是需要向前移动还是向后移动，要保证的就是时时刻刻链表里的所有的观察者的生命周期保证一致。
到这里其实注册观察者的方法以及分析完成了，刚才上面以及分析了`Lifecycle`的粘性特性，还剩一个**重入**没有说明。这里举一个例子
```
@Override
    protected void onResume() {
        super.onResume();
		//加入A-Observer
        getLifecycle().addObserver(new GenericLifecycleObserver() {
            @Override
            public void onStateChanged(LifecycleOwner lifecycleOwner, Lifecycle.Event event) {
                if(event == Lifecycle.Event.ON_START){
					//移出A-Observer
                    getLifecycle().removeObserver(this);
					//加入B-Observer
                    getLifecycle().addObserver(new GenericLifecycleObserver() {
                        @Override
                        public void onStateChanged(LifecycleOwner lifecycleOwner, Lifecycle.Event event) {
                            //todo 
                        }
                    });
                }
            }
        });
    }
```
可能比较绕，我自己也是想了很久才想通的，但是其实可以自己写个Demo试一试，并且打个断点，就会发现Google在这里的设计还是很巧妙的。这个例子简单介绍下：
>1.我们在Activity的onResume里面注册了一个观察者A
>2.在A的观察者的onStart的生命周期里面移出了A自己
>3.然后再A的观察者的onStart的生命周期里面加入了一个新的观察者B
那么这样生命周期会怎么回调呢？按照我们刚才的结论，我们在onResume里注册了A，那么A会直接**回溯**，回调`onCreate`和`onStart`。
然后这时候我们又注册了B观察者，这时候我们再看下`calculateTargetState`方法。
```
private State calculateTargetState(LifecycleObserver observer) {
        Entry<LifecycleObserver, LifecycleRegistry.ObserverWithState> previous = this.mObserverMap.ceil(observer);
        State siblingState = previous != null?((LifecycleRegistry.ObserverWithState)previous.getValue()).mState:null;
        State parentState = !this.mParentStates.isEmpty()?(State)this.mParentStates.get(this.mParentStates.size() - 1):null;
        return min(min(this.mState, siblingState), parentState);
    }
```
方法里的`mState`就是`onResume`，而A的生命周期（也就是Pre）是`onStart`，但是由于我们执行了`removeObserver`把A移出了，那么这时候其实`mObserverMap`里是一个空的Map，所以这时候`mParentStates`就出现用处了，先说下结论`mParentStates`会在观察者生命周期回调的执行内保存观察者，生命周期执行完成后移出观察者，所以一般情况下，这个`mParentStates`都是空的，但是像刚才举例的这个情况，我们就会发现，我们在A的生命周期内移出了A自身，就会导致没办法找到最新的观察者了，如果没有这个`mParentStates`，会出现什么问题呢？我们就会发现B会在A的`onStart`回调里回调`onCreate``onStart``onResume`，这就会出现一个逻辑性的错误，后注册的观察者的生命周期比之前注册的回调**超前**了。所以有了`mParentStates`后，`mParentStates`会保存A直到A的生命周期执行结束，所以这时候，B就只会执行`onCreate`和`onStart`的回调。这个就是我们说的重入问题。
```
private void forwardPass() {
        IteratorWithAdditions ascendingIterator = this.mObserverMap.iteratorWithAdditions();

        while(ascendingIterator.hasNext() && !this.mNewEventOccurred) {
            Entry<LifecycleObserver, LifecycleRegistry.ObserverWithState> entry = (Entry)ascendingIterator.next();
            LifecycleRegistry.ObserverWithState observer = (LifecycleRegistry.ObserverWithState)entry.getValue();

            while(observer.mState.compareTo(this.mState) < 0 && !this.mNewEventOccurred && this.mObserverMap.contains(entry.getKey())) {
				//放入mParentStates
                this.pushParentState(observer.mState);
                observer.dispatchEvent(this.mLifecycleOwner, upEvent(observer.mState));
				//移出mParentStates
                this.popParentState();
            }
        }

    }

    private void backwardPass() {
        Iterator descendingIterator = this.mObserverMap.descendingIterator();

        while(descendingIterator.hasNext() && !this.mNewEventOccurred) {
            Entry<LifecycleObserver, LifecycleRegistry.ObserverWithState> entry = (Entry)descendingIterator.next();
            LifecycleRegistry.ObserverWithState observer = (LifecycleRegistry.ObserverWithState)entry.getValue();

            while(observer.mState.compareTo(this.mState) > 0 && !this.mNewEventOccurred && this.mObserverMap.contains(entry.getKey())) {
                Event event = downEvent(observer.mState);
				//放入mParentStates
                this.pushParentState(getStateAfter(event));
                observer.dispatchEvent(this.mLifecycleOwner, event);
				//移出mParentStates
                this.popParentState();
            }
        }

    }
```
#### 正常的生命周期分发
上面观察和被观察的两种都介绍完了，我们再来看一下正常的生命周期分发，就会发现比较简单了，首先肯定是我们注入的空`Fragment`
```
public class ReportFragment extends Fragment {
    private static final String REPORT_FRAGMENT_TAG = "android.arch.lifecycle.LifecycleDispatcher.report_fragment_tag";
    private ReportFragment.ActivityInitializationListener mProcessListener;

    public ReportFragment() {
    }

    public void onDestroy() {
        super.onDestroy();
        this.dispatch(Event.ON_DESTROY);
        this.mProcessListener = null;
    }

    private void dispatch(Event event) {
        Activity activity = this.getActivity();
        if(activity instanceof LifecycleRegistryOwner) {
            ((LifecycleRegistryOwner)activity).getLifecycle().handleLifecycleEvent(event);
        } else {
            if(activity instanceof LifecycleOwner) {
                Lifecycle lifecycle = ((LifecycleOwner)activity).getLifecycle();
                if(lifecycle instanceof LifecycleRegistry) {
                    ((LifecycleRegistry)lifecycle).handleLifecycleEvent(event);
                }
            }

        }
    }
}
```
这里可以看到，在对应的生命周期执行`dispatch`方法，对应执行`LifecycleOwner`的`handleLifecycleEvent`方法，而我们知道实现`LifecycleOwner`的唯一类是`LifecycleRegistry`。
```
public void handleLifecycleEvent(Event event) {
        this.mState = getStateAfter(event);
        if(!this.mHandlingEvent && this.mAddingObserverCounter == 0) {
            this.mHandlingEvent = true;
			//关键方法同步
            this.sync();
            this.mHandlingEvent = false;
        } else {
            this.mNewEventOccurred = true;
        }
    }
```
可以看到就会执行刚才已经看过的同步方法，其实就是把循环，保证链表前后的生命周期和`mState`一致，不一致的话就会逐步通知生命周期。

### 总结
至此`Lifecycle`的生命周期分析完成了，我们对这个总体会有一个认知：
* Lifecycle感知生命周期的方式是通过注入一个空的Fragment实现
* 注入的方式有两种，一个是继承的Activity自动会注入，一个是在Application感知生命周期注入
* Lifecycle的初始化利用了ContentProvider实现无感知构建
* 注册观察者的时候会直接粘性的回调生命周期到当前的生命周期
* Lifecycle会保证注册的观察者按照注册顺序回调生命周期，并且考虑了重入的这种复杂情况
* 还在犹豫什么？赶快体验吧~
