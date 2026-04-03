>本系列博客基于androidx-2.2.0版本
[【JetPack系列】——Lifecycle源码分析](https://www.jianshu.com/p/175a2138f5e2)
[【JetPack系列】——LiveData源码解析](https://www.jianshu.com/p/b047bcfb2a04)
[【JetPack系列】——ViewModel源码解析](https://www.jianshu.com/p/1715d7826191)
### 前言
[前一篇博客](https://www.jianshu.com/p/175a2138f5e2)分析了LiveCycle的源码分析，有了LiveCycle的了解，对于我们LiveData就非常容易了。首先我们先了解下LiveData是什么，同样这里放上Google的官方介绍[链接](https://developer.android.com/topic/libraries/architecture/livedata)
>LiveData is an observable data holder class. Unlike a regular observable, LiveData is lifecycle-aware, meaning it respects the lifecycle of other app components, such as activities, fragments, or services. This awareness ensures LiveData only updates app component observers that are in an active lifecycle state.

从介绍可以看到，LiveData同样也是观察者模式的应用，只不过用于通知数据更新的，而相较于Rxjava和EventBus这类消息的事件总线的框架不同的是，LiveData正如其名字那样具有**Live**感知生命周期的能力，它只会在观察者处于**active**的状态下才会通知数据改变。
### 源码分析
```
class NameViewModel : ViewModel() {

    // Create a LiveData with a String
    val currentName: MutableLiveData<String> by lazy {
        MutableLiveData<String>()
    }

    // Rest of the ViewModel...
}

class NameActivity : AppCompatActivity() {

    // Use the 'by viewModels()' Kotlin property delegate
    // from the activity-ktx artifact
    private val model: NameViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Other code to setup the activity...

        // Create the observer which updates the UI.
        val nameObserver = Observer<String> { newName ->
            // Update the UI, in this case, a TextView.
            nameTextView.text = newName
        }

        // Observe the LiveData, passing in this activity as the LifecycleOwner and the observer.
        model.currentName.observe(this, nameObserver)
    }
}
```
看下官方的Demo介绍，可以看到使用很简单，我们首先在`ViewModel`中构造一个`LiveData`，然后在`Activity`中使用即可。以为`LiveData`的构造函数这里没有什么特殊处理，所以我们这里就看下观察的地方。
#### 观察LiveData
```
@MainThread
    public void observe(@NonNull LifecycleOwner owner, @NonNull Observer<? super T> observer) {
        assertMainThread("observe");
        if (owner.getLifecycle().getCurrentState() == DESTROYED) {
            // ignore
            return;
        }
		//包装一层
        LifecycleBoundObserver wrapper = new LifecycleBoundObserver(owner, observer);
        ObserverWrapper existing = mObservers.putIfAbsent(observer, wrapper);
        if (existing != null && !existing.isAttachedTo(owner)) {
            throw new IllegalArgumentException("Cannot add the same observer"
                    + " with different lifecycles");
        }
        if (existing != null) {
            return;
        }
        owner.getLifecycle().addObserver(wrapper);
    }
```
可以看到没有什么特别复杂的处理，如果看过[上一篇博客](https://www.jianshu.com/p/175a2138f5e2)的话，可以看到这里应该会很熟悉，因为处理的逻辑很相似。
首先看到没有`LiveData`对于生命周期的处理这里已经展现出来了，首先方法的入参有一个`LivecycleOwner`,也就是生命周期的感知者，对应到`Activity`和`Fragment`。如果是在`Destroy`的时候，那么这里首先就会拦截，不允许注册`LiveData`了。
后面这里使用了一个包装类`LifecycleBoundObserver`，来包装我们的`LivecycleOwner`和`Observer`
```
class LifecycleBoundObserver extends ObserverWrapper implements LifecycleEventObserver {
        @NonNull
        final LifecycleOwner mOwner;

        LifecycleBoundObserver(@NonNull LifecycleOwner owner, Observer<? super T> observer) {
            super(observer);
            mOwner = owner;
        }

        @Override
        boolean shouldBeActive() {
            return mOwner.getLifecycle().getCurrentState().isAtLeast(STARTED);
        }

        @Override
        public void onStateChanged(@NonNull LifecycleOwner source,
                @NonNull Lifecycle.Event event) {
            if (mOwner.getLifecycle().getCurrentState() == DESTROYED) {
                removeObserver(mObserver);
                return;
            }
            activeStateChanged(shouldBeActive());
        }

        @Override
        boolean isAttachedTo(LifecycleOwner owner) {
            return mOwner == owner;
        }

        @Override
        void detachObserver() {
            mOwner.getLifecycle().removeObserver(this);
        }
    }

private abstract class ObserverWrapper {
        final Observer<? super T> mObserver;
        boolean mActive;
        int mLastVersion = START_VERSION;

        ObserverWrapper(Observer<? super T> observer) {
            mObserver = observer;
        }

        abstract boolean shouldBeActive();

        boolean isAttachedTo(LifecycleOwner owner) {
            return false;
        }

        void detachObserver() {
        }

        void activeStateChanged(boolean newActive) {
            if (newActive == mActive) {
                return;
            }
            // immediately set active state, so we'd never dispatch anything to inactive
            // owner
            mActive = newActive;
            boolean wasInactive = LiveData.this.mActiveCount == 0;
            LiveData.this.mActiveCount += mActive ? 1 : -1;
            if (wasInactive && mActive) {
                onActive();
            }
            if (LiveData.this.mActiveCount == 0 && !mActive) {
                onInactive();
            }
            if (mActive) {
                dispatchingValue(this);
            }
        }
    }
```
代码没有特别复杂，这里先不展开介绍，后面具体使用的时候再展开介绍。大体浏览下来的第一感觉就是这个类的作用就是将`LifecycleOwner`和`Observer`两个类包装起来，并且加上了生命周期的判断处理。
接下来就比较简单了，首先判断这个观察者有没有被加入过，如果加入过这里就抛异常，然后加入`LifecycleOwner`观察。所以观察的地方这里就分析完了，没有太特殊的逻辑。
#### LiveData更新
```
public class MutableLiveData<T> extends LiveData<T> {

    /**
     * Creates a MutableLiveData initialized with the given {@code value}.
     *
     * @param value initial value
     */
    public MutableLiveData(T value) {
        super(value);
    }

    /**
     * Creates a MutableLiveData with no value assigned to it.
     */
    public MutableLiveData() {
        super();
    }

    @Override
    public void postValue(T value) {
        super.postValue(value);
    }

    @Override
    public void setValue(T value) {
        super.setValue(value);
    }
}
```
因为这里是介绍原理，所以就看一下我们经常使用的`MutableLiveData`。可以看到有两个方法，一个是`setValue`一个是`postValue`。看到这个名字我们应该会非常敏感，因为一个是`post`和我们使用Handler里使用的`post`很相似。
```
protected void postValue(T value) {
        boolean postTask;
        synchronized (mDataLock) {
            postTask = mPendingData == NOT_SET;
            mPendingData = value;
        }
        if (!postTask) {
            return;
        }
        ArchTaskExecutor.getInstance().postToMainThread(mPostValueRunnable);
    }

private final Runnable mPostValueRunnable = new Runnable() {
        @SuppressWarnings("unchecked")
        @Override
        public void run() {
            Object newValue;
            synchronized (mDataLock) {
                newValue = mPendingData;
                mPendingData = NOT_SET;
            }
            setValue((T) newValue);
        }
    };
```
可以看到这里其实最后使用的还是`setValue`，只不过这里使用`Handler.post`到了主线程（没有放具体代码，但是比较简单），但是这里有一个点需要注意下，因为这里可以看到因为是用post到主线程，如果我们子线程连续两次执行`postValue`，也就是在`runnable`还没有执行的时候，我们多次修改`mPendingData`的值，那么其实最后可能最终得到的是最后一次的值，因为并不是每一次调用`postValue`都会执行`Handler.post`操作，这个需要我们注意下。
所以剩下的我们就来看下`setValue`的实现。
```
 @MainThread
    protected void setValue(T value) {
        assertMainThread("setValue");
        mVersion++;
        mData = value;
        dispatchingValue(null);
    }
```
没有太复杂的逻辑，这里有个版本号的逻辑，每次设置value的时候都会增加一个版本号，核心逻辑在`dispatchingValue`
```
void dispatchingValue(@Nullable ObserverWrapper initiator) {
        if (mDispatchingValue) {
			//防止重入
            mDispatchInvalidated = true;
            return;
        }
        mDispatchingValue = true;
        do {
            mDispatchInvalidated = false;
            if (initiator != null) {
                considerNotify(initiator);
                initiator = null;
            } else {
                for (Iterator<Map.Entry<Observer<? super T>, ObserverWrapper>> iterator =
                        mObservers.iteratorWithAdditions(); iterator.hasNext(); ) {
                    considerNotify(iterator.next().getValue());
                    if (mDispatchInvalidated) {
                        break;
                    }
                }
            }
        } while (mDispatchInvalidated);
        mDispatchingValue = false;
    }
```
其次这里可以看到传入的参数是否为null也是有差异的，但最终执行的都是`considerNotify`方法，从代码可以看出来，如果传入的不为null，则只是单纯刷新一个观察者，如果传入的为null，则遍历所有的观察者进行刷新。那么我们来看下有哪些地方调用了这个方法。
![引用](https://upload-images.jianshu.io/upload_images/7866586-d3e1fa85ba08d951.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

可以看到刚好有两处，一个传入的是this，一个传入的是null对象。
```
@MainThread
    protected void setValue(T value) {
        assertMainThread("setValue");
        mVersion++;
        mData = value;
        dispatchingValue(null);
    }

void activeStateChanged(boolean newActive) {
            if (newActive == mActive) {
                return;
            }
            // immediately set active state, so we'd never dispatch anything to inactive
            // owner
            mActive = newActive;
            boolean wasInactive = LiveData.this.mActiveCount == 0;
            LiveData.this.mActiveCount += mActive ? 1 : -1;
            if (wasInactive && mActive) {
                onActive();
            }
            if (LiveData.this.mActiveCount == 0 && !mActive) {
                onInactive();
            }
            if (mActive) {
                dispatchingValue(this);
            }
        }
```
`setValue`这里就不说了，`activeStateChange`这里可以看下，从方法的名字上也很好理解，就是在状态变成活跃的时候，会调用，并且传入this对象，仅刷新一个观察者，那么我们来看下调用这个方法的地方，验证一下我们的想法。
```
@Override
        public void onStateChanged(@NonNull LifecycleOwner source,
                @NonNull Lifecycle.Event event) {
            if (mOwner.getLifecycle().getCurrentState() == DESTROYED) {
                removeObserver(mObserver);
                return;
            }
            activeStateChanged(shouldBeActive());
        }
```
可以看到回到我们[第一篇博客](https://www.jianshu.com/p/175a2138f5e2)分析的地方，我们的观察者在接受状态回调的通知的时候，会首先看下当前的状态是不是`Destroy`，如果是的话则会执行移出观察者，所有这里我们可以可以得出一个结论：**LiveData**在Destroy的时候会移除自身，并且不会收到回调，所以我们也不用担心内存泄漏和空指针的情况发生。
```
private void considerNotify(ObserverWrapper observer) {
        if (!observer.mActive) {
            return;
        }
        // Check latest state b4 dispatch. Maybe it changed state but we didn't get the event yet.
        //
        // we still first check observer.active to keep it as the entrance for events. So even if
        // the observer moved to an active state, if we've not received that event, we better not
        // notify for a more predictable notification order.
        if (!observer.shouldBeActive()) {
            observer.activeStateChanged(false);
            return;
        }
        if (observer.mLastVersion >= mVersion) {
            return;
        }
        observer.mLastVersion = mVersion;
        observer.mObserver.onChanged((T) mData);
    }
```
首先可以看到这里又加了一层判断，如果当前观察者的状态不是活跃的，那么就不会执行通知，而这个`mActive`对象在什么地方赋值呢。没错，又回到我们刚才分析的`activeStateChanged`方法，那么可以看到`mActive`的对象的值是由`shouldBeActive()`方法决定的。
```
@Override
        boolean shouldBeActive() {
            return mOwner.getLifecycle().getCurrentState().isAtLeast(STARTED);
        }
```
所以可以看到，对于**活跃**的定义就我们的观察者的状态必须是大于等于`onStart`生命周期。
继续看下面的逻辑，其实这块逻辑我一开始是有点困惑的，而且看了网上很多关于LiveData的源码分析博客，都对这里没有提及，或者一掠而过。
```
// Check latest state b4 dispatch. Maybe it changed state but we didn't get the event yet.
        //
        // we still first check observer.active to keep it as the entrance for events. So even if
        // the observer moved to an active state, if we've not received that event, we better not
        // notify for a more predictable notification order.
        if (!observer.shouldBeActive()) {
            observer.activeStateChanged(false);
            return;
        }
```
其实可以看到这里注释也很多，这里我困惑的地方是这样的，刚才前面已经做了`mActive`的状态判断，那么为什么这里又要做一个关于`active`状态判断呢，会不会有些多余？
那么这里我们就看一下二者的区别，一个是对于`mActive`的判断，一个是对`Onwer`的生命周期的判断，能够走到这个if条件里面的case，说明当前观察者是活跃状态，但是被观察者不是活跃状态。那么这里我们就可以想到一个case了。
>假如我们的`Activity`以及是Stop状态，我们此时的注册的观察者有A,B,C(LiveData),其中C是LiveData的的绑定的观察者，如果我们在A的生命周期回调的地方，调用C的LiveData的setValue方法，那么就会出现我们C的状态还没有接收到stop的状态，需要执行setValue方法，但是这时候其实`Activity`其实已经是stop状态了，那么就和`LiveData`的初心违背了。

所以这里这个判断就是处理这种特殊case的，也就是嵌套通知或者说是重入，其实看过其[第一篇博客](https://www.jianshu.com/p/175a2138f5e2)
的应该也会发现有关于重入的概念，我们会发现Google在处理观察者模式的时候，对于重入的处理其实是值得我们学习的，往往我们自己设计的观察者模式是忽略这种情况的。
后面这里有个关于版本的判断，其实一开始我是忽略版本的这块逻辑的，因为我没发现这块的太具体的作用。但是最新又想了想这块还是需要特殊说明的。看过前面的分析我们应该会发现`LiveData`其实是有一个特性的，那就是粘性事件，比如这里举一个例子。
```
@Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
		//还没监听，先设置值
        liveDataViewModel.getLiveDate().setValue(10);
		//再监听
        liveDataViewModel.getLiveDate().observe(this, new Observer<Integer>() {
            @Override
            public void onChanged(Integer integer) {
                Log.i("LiveData-Value", "" + integer);
            }
        });
    }
```
这里我们先调用了LiveData.setValue方法，设置value为10，然后再注册一个观察者，那么这个通知会收到吗？会在什么时候收到呢？
**这里先给下结论，会收到通知，会在onStart回调收到之后收到通知**
1.其实具体的原来上面都已经分析到了，只不过没有结合具体的例子分析，这里就简单分析下。
首先我们调用`setValue`的时候，会将LiveData内部的value设置为10，其次会将version++，也就是1，然后本来应该通知观察LiveData的观察者刷新数据的，因为此时没有观察者，并且就算有，此时也不是`active`状态，所以也不会通知。
2.然后我们调用`Observer`方法，注册了一个LiveData观察者，按照第[第一篇博客](https://www.jianshu.com/p/175a2138f5e2)的分析，我们会回溯生命周期，但是这里其实是在onCreate注册的，和Owner保持同步，所以也不会执行生命周期的同步，也就是单纯的注册，也就是说我们在注册了观察者后不会立即收到回调。
3.接着我们Activity在收到onStart生命周期回调后会通知观察者，这时候就会通知我们刚才注册的观察者了，这时候**由于观察者的状态会从不活跃变成活跃**。
```
@Override
        public void onStateChanged(@NonNull LifecycleOwner source,
                @NonNull Lifecycle.Event event) {
            if (mOwner.getLifecycle().getCurrentState() == DESTROYED) {
                removeObserver(mObserver);
                return;
            }
            activeStateChanged(shouldBeActive());
        }
```
所以就会执行到我们刚才分析的地方，这里最后就会执行我们刚才提到的版本判断，因为我们注册到观察者的version初始值是-1，而当前LiveData的version是1，所以就会执行onChange方法，执行通知刷新。
这样整个流程就串起来了。
### 总结
LivaData我们可以看到是一个很轻量级的数据驱动框架，并且结合Lifecycle，使得其有了感知生命周期的能力，所以我们可以得出LiveData有以下特性：
* 感知生命周期
* 不会有内存泄漏，自动在Destroy的时候解绑
* 支持粘性事件
* 支持嵌套事件
* 轻量级
* 支持重入
* 不支持跨页面使用（个人不倾向于这样使用）
综上，可以看出LiveData还是一个很优秀 的框架的，大家快去使用吧~
