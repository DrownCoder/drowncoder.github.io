>本系列博客基于androidx-2.2.0版本
[【JetPack系列】——Lifecycle源码分析](https://www.jianshu.com/p/175a2138f5e2)
[【JetPack系列】——LiveData源码解析](https://www.jianshu.com/p/b047bcfb2a04)
[【JetPack系列】——ViewModel源码解析](https://www.jianshu.com/p/1715d7826191)
### 前言
前两篇博客分析了Lifecycle，LiveData，本篇博客分析**MVVM三剑客**的终篇ViewModel，但从ViewModel类本身，其实没有太多要分析的东西，看了源码会发现类本身很简单，而我们对于ViewModel主要关注的是两个地方。
* 1.数据共享，支持Activity内所有Fragment共享数据
* 2.数据恢复，支持内存级别的Activity数据恢复保存数据

### 源码分析
本篇博客基于androidx.lifecycle:lifecycle-viewmodel-ktx:2.2.0，起初本来想分析android版本的，但是发现androidx版本相较于低版本虽然原理没有本质的改变，但是增加了许多其他的逻辑。
#### 初始化ViewModel
既然**数据共享**特性，那么也就是说我们在Activity的任意位置拿到的ViewModel是唯一的，也就是**Activity单例**，在看了ViewModel的创建过程后，就会理解了为什么ViewModel能做到这一特性。我们创建ViewModel的方式其实有两种，但是一种已经被标记为过时了。
```
	ViewModelProvider(this).get(LiveDataViewModel.class);
	//过时
	ViewModelProviders.of(this).get(LiveDataViewModel.class);
```
其实两个没有实质的区别，只是ViewModelProviders把ViewModelProvider包了一层，后面Google估计发现这么做没有什么必要，所以就将ViewModelProviders废弃了，直接建议我们使用ViewModelProvider。
```
public ViewModelProvider(@NonNull ViewModelStoreOwner owner) {
        this(owner.getViewModelStore(), owner instanceof HasDefaultViewModelProviderFactory
                ? ((HasDefaultViewModelProviderFactory) owner).getDefaultViewModelProviderFactory()
                : NewInstanceFactory.getInstance());
    }
public ViewModelProvider(@NonNull ViewModelStore store, @NonNull Factory factory) {
        mFactory = factory;
        mViewModelStore = store;
    }
```
首先看一下构造函数，其实单从逻辑来看，就是两个简单的赋值操作，但从类来看，这里面涉及到的类，已经是我们这回要理解的80%了......所以我们一个一个来看。
```
public interface ViewModelStoreOwner {
    /**
     * Returns owned {@link ViewModelStore}
     *
     * @return a {@code ViewModelStore}
     */
    @NonNull
    ViewModelStore getViewModelStore();
}
```
首先看到ViewModelStoreOwner，单从名字来看就知道ViewModelStore的提供者，从实现类来看也可以看到ComponentActivity和Fragment都已经实现了这个接口，所以我们传入的Activity和Fragment满足条件。分别来看下两处的实现逻辑。
```
 @NonNull
    @Override
    public ViewModelStore getViewModelStore() {
        if (getApplication() == null) {
            throw new IllegalStateException("Your activity is not yet attached to the "
                    + "Application instance. You can't request ViewModel before onCreate call.");
        }
        if (mViewModelStore == null) {
			//状态恢复
            NonConfigurationInstances nc =
                    (NonConfigurationInstances) getLastNonConfigurationInstance();
            if (nc != null) {
                // Restore the ViewModelStore from NonConfigurationInstances
                mViewModelStore = nc.viewModelStore;
            }
            if (mViewModelStore == null) {
                mViewModelStore = new ViewModelStore();
            }
        }
        return mViewModelStore;
    }
```
Activity的实现其实可以看到，先暂时抛开注释的状态恢复的逻辑，所以可以看到就是一个Activity的成员变量，没有就new了一个。
```
public ViewModelStore getViewModelStore() {
        if (mFragmentManager == null) {
            throw new IllegalStateException("Can't access ViewModels from detached fragment");
        }
        return mFragmentManager.getViewModelStore(this);
    }

private FragmentManagerViewModel mNonConfig;

@NonNull
    ViewModelStore getViewModelStore(@NonNull Fragment f) {
        return mNonConfig.getViewModelStore(f);
    }
```
Fragment可以看到使用的是FragmentManager，所以这里我们应该能够意识到Fragment内部到ViewModel其实是**Fragment单例**的，这里其实有一个地方挺有意思，这里使用了`mNoConfig`对象，而这个对象其实就是一个ViewModel，这里就有点**鸡生蛋，蛋生鸡**的问题，我们在研究ViewModel的创建，但是ViewModel的创建又用到了ViewModel。
```
 // Get the FragmentManagerViewModel
        if (parent != null) {
            mNonConfig = parent.mFragmentManager.getChildNonConfig(parent);
        } else if (host instanceof ViewModelStoreOwner) {
            ViewModelStore viewModelStore = ((ViewModelStoreOwner) host).getViewModelStore();
            mNonConfig = FragmentManagerViewModel.getInstance(viewModelStore);
        } else {
            mNonConfig = new FragmentManagerViewModel(false);
        }
```
而这里创建的逻辑我们可以看下，不同归属级的Fragment就会使用不同的创建，也是刚才那个结论：**Activity获取到的ViewModel是Activity级别的单例，Fragment获取到的ViewModel是Fragment单例**，Fragment嵌套，子Fragment和父Fragment获取的不是同一个ViewModel。
```
@NonNull
    ViewModelStore getViewModelStore(@NonNull Fragment f) {
        ViewModelStore viewModelStore = mViewModelStores.get(f.mWho);
        if (viewModelStore == null) {
            viewModelStore = new ViewModelStore();
            mViewModelStores.put(f.mWho, viewModelStore);
        }
        return viewModelStore;
    }
```
而这里的创建逻辑也是拿一个Map保存。这样ViewModelStore的创建逻辑就分析完了，接下来看另一个参数，Factory。
```
public ViewModelProvider(@NonNull ViewModelStoreOwner owner) {
        this(owner.getViewModelStore(), owner instanceof HasDefaultViewModelProviderFactory
                ? ((HasDefaultViewModelProviderFactory) owner).getDefaultViewModelProviderFactory()
                : NewInstanceFactory.getInstance());
    }
```
首先来看一下Factory的结构，既然是工厂，肯定是一个创建的地方。
```
public interface Factory {
        /**
         * Creates a new instance of the given {@code Class}.
         * <p>
         *
         * @param modelClass a {@code Class} whose instance is requested
         * @param <T>        The type parameter for the ViewModel.
         * @return a newly created ViewModel
         */
        @NonNull
        <T extends ViewModel> T create(@NonNull Class<T> modelClass);
    }
```
确实就是我们创建ViewModel最终的地方，那么同样这里如果Owner实现了`HasDefaultViewModelProviderFactory`接口，会调用`getDefaultViewModelProviderFactory()`方法，同样Activity和Fragment都实现了这个接口，这里就只看Activity的逻辑吧，因为刚才分析ViewModelStore的时候我们就发现了Activity和Fragment的不同只是持有对象的不同，逻辑上没有本质区别。
```
    @Override
    public ViewModelProvider.Factory getDefaultViewModelProviderFactory() {
        if (getApplication() == null) {
            throw new IllegalStateException("Your activity is not yet attached to the "
                    + "Application instance. You can't request ViewModel before onCreate call.");
        }
        if (mDefaultFactory == null) {
            mDefaultFactory = new SavedStateViewModelFactory(
                    getApplication(),
                    this,
                    getIntent() != null ? getIntent().getExtras() : null);
        }
        return mDefaultFactory;
    }
```
果然是一个工厂，但是这里这个工厂的名字，我们看到了应该会很敏感，这是一个和状态恢复有关的工厂，那么我们来看一下create方法。
```
private static final Class<?>[] ANDROID_VIEWMODEL_SIGNATURE = new Class[]{Application.class,
            SavedStateHandle.class};
    private static final Class<?>[] VIEWMODEL_SIGNATURE = new Class[]{SavedStateHandle.class};

@NonNull
    @Override
    public <T extends ViewModel> T create(@NonNull String key, @NonNull Class<T> modelClass) {
        boolean isAndroidViewModel = AndroidViewModel.class.isAssignableFrom(modelClass);
        Constructor<T> constructor;
		//是否是ActivityViewModel
        if (isAndroidViewModel && mApplication != null) {
			//通过参数查找构造函数
            constructor = findMatchingConstructor(modelClass, ANDROID_VIEWMODEL_SIGNATURE);
        } else {
            constructor = findMatchingConstructor(modelClass, VIEWMODEL_SIGNATURE);
        }
        // doesn't need SavedStateHandle、
		//没找到直接创建
        if (constructor == null) {
            return mFactory.create(modelClass);
        }
		//这里找到了会传一个SavedStateHandleController到构造函数中
        SavedStateHandleController controller = SavedStateHandleController.create(
                mSavedStateRegistry, mLifecycle, key, mDefaultArgs);
        try {
            T viewmodel;
            if (isAndroidViewModel && mApplication != null) {
                viewmodel = constructor.newInstance(mApplication, controller.getHandle());
            } else {
                viewmodel = constructor.newInstance(controller.getHandle());
            }
            viewmodel.setTagIfAbsent(TAG_SAVED_STATE_HANDLE_CONTROLLER, controller);
            return viewmodel;
        } catch (IllegalAccessException e) {
            throw new RuntimeException("Failed to access " + modelClass, e);
        } catch (InstantiationException e) {
            throw new RuntimeException("A " + modelClass + " cannot be instantiated.", e);
        } catch (InvocationTargetException e) {
            throw new RuntimeException("An exception happened in constructor of "
                    + modelClass, e.getCause());
        }
    }

private static <T> Constructor<T> findMatchingConstructor(Class<T> modelClass,
            Class<?>[] signature) {
        for (Constructor<?> constructor : modelClass.getConstructors()) {
            Class<?>[] parameterTypes = constructor.getParameterTypes();
            if (Arrays.equals(signature, parameterTypes)) {
                return (Constructor<T>) constructor;
            }
        }
        return null;
    }
```
这里我一开始很困惑，我们理解到ViewModel构造函数是没有任何参数的，或者是我们使用Application类型的ViewModel，会有一个Application参数，那么这里`SavedStateHandle`是哪里来的呢？后面看了网上的一些分析发下你，这个应该是Google针对ViewModel的状态恢复提供的一个新的特性类，具体后面一个章节再来分析，这里还是先聚焦一下ViewModel共享的问题。所以，这里如果不考虑状态恢复，肯定找不到构造器，会走到`Factory.create(modelClass)`中。
```
public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {
            //noinspection TryWithIdenticalCatches
            try {
                return modelClass.newInstance();
            } catch (InstantiationException e) {
                throw new RuntimeException("Cannot create an instance of " + modelClass, e);
            } catch (IllegalAccessException e) {
                throw new RuntimeException("Cannot create an instance of " + modelClass, e);
            }
        }

@NonNull
        @Override
        public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {
            if (AndroidViewModel.class.isAssignableFrom(modelClass)) {
                //noinspection TryWithIdenticalCatches
                try {
                    return modelClass.getConstructor(Application.class).newInstance(mApplication);
                } catch (NoSuchMethodException e) {
                    throw new RuntimeException("Cannot create an instance of " + modelClass, e);
                } catch (IllegalAccessException e) {
                    throw new RuntimeException("Cannot create an instance of " + modelClass, e);
                } catch (InstantiationException e) {
                    throw new RuntimeException("Cannot create an instance of " + modelClass, e);
                } catch (InvocationTargetException e) {
                    throw new RuntimeException("Cannot create an instance of " + modelClass, e);
                }
            }
            return super.create(modelClass);
        }
```
没啥特殊的处理，就是通过反射构造器，来初始化对象。所以到这里我们对于ViewModelProvider的初始化分析完了，可以总结几点：
* 1.都是利用Activity/Fragment的成员变量来进行创建
* 2.使用的是反射构造器进行创建，其实从这里已经大概能看出为什么能够实现**Activity单例**或者说**Fragment单例**，其实就是拿一个东西存储着，所以获取的地方都是相同的地方，所以拿到的就是同一个对象，接下来来看一下最终获取对象的方法`get`来验证一下我们的猜想。
```
@NonNull
    @MainThread
    public <T extends ViewModel> T get(@NonNull Class<T> modelClass) {
        String canonicalName = modelClass.getCanonicalName();
        if (canonicalName == null) {
            throw new IllegalArgumentException("Local and anonymous classes can not be ViewModels");
        }
        return get(DEFAULT_KEY + ":" + canonicalName, modelClass);
    }

public <T extends ViewModel> T get(@NonNull String key, @NonNull Class<T> modelClass) {
        ViewModel viewModel = mViewModelStore.get(key);

        if (modelClass.isInstance(viewModel)) {
            if (mFactory instanceof OnRequeryFactory) {
                ((OnRequeryFactory) mFactory).onRequery(viewModel);
            }
            return (T) viewModel;
        } else {
            //noinspection StatementWithEmptyBody
            if (viewModel != null) {
                // TODO: log a warning.
            }
        }
        if (mFactory instanceof KeyedFactory) {
            viewModel = ((KeyedFactory) (mFactory)).create(key, modelClass);
        } else {
            viewModel = (mFactory).create(modelClass);
        }
        mViewModelStore.put(key, viewModel);
        return (T) viewModel;
    }
```
这里简答看下，其实就会发现，就是刚才拿到的ViewModelStore，来获取VIewModel，如果没有的话就会通过Factory构造一个ViewModel，并且存到ViewModelStore里面。
```
public class ViewModelStore {

    private final HashMap<String, ViewModel> mMap = new HashMap<>();

    final void put(String key, ViewModel viewModel) {
        ViewModel oldViewModel = mMap.put(key, viewModel);
        if (oldViewModel != null) {
            oldViewModel.onCleared();
        }
    }

    final ViewModel get(String key) {
        return mMap.get(key);
    }

    Set<String> keys() {
        return new HashSet<>(mMap.keySet());
    }

    /**
     *  Clears internal storage and notifies ViewModels that they are no longer used.
     */
    public final void clear() {
        for (ViewModel vm : mMap.values()) {
            vm.clear();
        }
        mMap.clear();
    }
}

```
而ViewModelStore的结构也很简单，就是一个Map的结构。所以到这里我们关于ViewModel的创建和获取其实已经有了一个大概的了解。
* 1.ViewModel通过反射构造器创建
* 2.ViewModel在ViewModelStore中存储，是一个Map的结构。
* 3.ViewModelStore是一个成员变量，对于Activity层级来说，是Activity的成员变量，对于Fragment来说，是FragmentManager的成员变量。
基于以上几点，所以可以达到ViewModel的**Activity单例**的特性。
#### ViewModel的状态恢复
ViewModel的数据保存一直是Google推出ViewModel后主打的概念，但我一直感觉ViewModel比较核心的应该是他的Activity单例，有了这个特性，才能达到LiveData的数据共享，进而达到数据驱动的思想。但反观ViewModel的状态恢复的源码，会发现Google在不停调整他的实现原理，这是我感觉比较少见的，也可见Google对于他的重视程度。ViewModel的状态恢复原理经历了三个阶段：
* 1.利用Fragment的setRetainInstance特性
* 2.利用Activity的onRetainNonConfigurationInstance特性
* 3.利用Activity的onSaveInstance特性

刚好配合ViewModel的状态恢复，我们从中也可以学到状态恢复的几种方式。首先看下这三种方式，有什么区别呢？这里方式一篇我感觉很不错的博客，里面比较详细的讲解了状态恢复的几个总结。[ViewModel 这些知识点你都知道吗?](https://www.jianshu.com/p/39ef3e0a5829?utm_source=desktop&utm_medium=timeline)
![对比](https://upload-images.jianshu.io/upload_images/7866586-61436409c3b683bc.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

上图也是来源于这篇博客，我感觉写的很好，很清晰的展示了三种的区别，若侵立删~
回到状态恢复，从上面的介绍我们会发现ViewModel的状态恢复持久化越来越强，从最初的内存级别到现在的磁盘级别，那么接下来我们就从源码的角度看下三种的实现方式。
```
public static ViewModelStore of(@NonNull Fragment fragment) {
        if (fragment instanceof ViewModelStoreOwner) {
            return ((ViewModelStoreOwner) fragment).getViewModelStore();
        }
        return holderFragmentFor(fragment).getViewModelStore();
    }

public static HolderFragment holderFragmentFor(Fragment fragment) {
        return sHolderFragmentManager.holderFragmentFor(fragment);
    }
```
早期的ViewModel我们前面提到了，是使用`ViewModelProviders.of(this).get(LiveDataViewModel.class);`方式创建的，可以看到，最终是委托了一个叫`HolderFragment`的对象。
```
public class HolderFragment extends Fragment implements ViewModelStoreOwner {
    private static final String LOG_TAG = "ViewModelStores";

    private static final HolderFragmentManager sHolderFragmentManager = new HolderFragmentManager();

    /**
     * @hide
     */
    @RestrictTo(RestrictTo.Scope.LIBRARY_GROUP)
    public static final String HOLDER_TAG =
            "android.arch.lifecycle.state.StateProviderHolderFragment";

    private ViewModelStore mViewModelStore = new ViewModelStore();

    public HolderFragment() {
        setRetainInstance(true);
    }
}
```
而看一下这个类，我们就会发现，这是一个Fragment，但是在构造函数的时候，会调用`setRetainInstance(true);`方法，这个方法平时我们使用Fragment的时候基本上没有接触过，我们看一下这个方法的注释。
```
/**
     * Control whether a fragment instance is retained across Activity
     * re-creation (such as from a configuration change).  This can only
     * be used with fragments not in the back stack.  If set, the fragment
     * lifecycle will be slightly different when an activity is recreated:
     * <ul>
     * <li> {@link #onDestroy()} will not be called (but {@link #onDetach()} still
     * will be, because the fragment is being detached from its current activity).
     * <li> {@link #onCreate(Bundle)} will not be called since the fragment
     * is not being re-created.
     * <li> {@link #onAttach(Activity)} and {@link #onActivityCreated(Bundle)} <b>will</b>
     * still be called.
     * </ul>
     */
    public void setRetainInstance(boolean retain) {
        mRetainInstance = retain;
    }
```
注释讲的比较明白了，其实这个Fragment实例会在Activity发生配置改变，例如旋转等，不会被销毁重新创建，如果深入源码，其实简单说，就是在配置发生改变的时候，系统会销毁所有的Fragment重建，但是会优先判断一下这个变量的值，如果为true，则不销毁，直接复用，这里就不展开了。这里就可以先得到一个结论。
>最早的ViewModel是只支持内存级别的状态恢复，并且只支持配置发生改变，如果内存不足场景导致Activity被销毁，ViewModel是无法保证数据完整的。
```
/**
     * Retain all appropriate non-config state.  You can NOT
     * override this yourself!  Use a {@link androidx.lifecycle.ViewModel} if you want to
     * retain your own non config state.
     */
    @Override
    @Nullable
    @SuppressWarnings("deprecation")
    public final Object onRetainNonConfigurationInstance() {
        // Maintain backward compatibility.
        Object custom = onRetainCustomNonConfigurationInstance();

        ViewModelStore viewModelStore = mViewModelStore;
        if (viewModelStore == null) {
            // No one called getViewModelStore(), so see if there was an existing
            // ViewModelStore from our last NonConfigurationInstance
            NonConfigurationInstances nc =
                    (NonConfigurationInstances) getLastNonConfigurationInstance();
            if (nc != null) {
                viewModelStore = nc.viewModelStore;
            }
        }

        if (viewModelStore == null && custom == null) {
            return null;
        }

        NonConfigurationInstances nci = new NonConfigurationInstances();
        nci.custom = custom;
        nci.viewModelStore = viewModelStore;
        return nci;
    }
```
这个方法原来一直没有注意到，原来一直以为状态恢复自由onSaveInstance，但看了下官方的文档，发现这个和`setRetainInstance`效果上没有太大的区别，只是从Fragment抽离了这部分逻辑，从架构层面来看，确实本来状态恢复是属于Activity的职责，但却需要Fragment来实现这个特性，而Activity自身却没有这个特性。从源码中我们可以看到，这里其实就是返回了一个Object对象，而这个方法是一个final类型的，表示我们不能重写，我甚至怀疑这个是Google专门为ViewModel开的一个口子，从注释中可以看到这个是专门为ViewModel打造的，不知道是不是这样。但逻辑上其实就很简单，拿`NonConfigurationInstances`包装了一层，将我们上面分析的ViewModelStore给存了起来。
```
 public ViewModelStore getViewModelStore() {
        if (getApplication() == null) {
            throw new IllegalStateException("Your activity is not yet attached to the "
                    + "Application instance. You can't request ViewModel before onCreate call.");
        }
        if (mViewModelStore == null) {
            NonConfigurationInstances nc =
                    (NonConfigurationInstances) getLastNonConfigurationInstance();
            if (nc != null) {
                // Restore the ViewModelStore from NonConfigurationInstances
                mViewModelStore = nc.viewModelStore;
            }
            if (mViewModelStore == null) {
                mViewModelStore = new ViewModelStore();
            }
        }
        return mViewModelStore;
    }
```
而前面我们分析到的获取ViewModelStore的地方，就会从这里取出存储的ViewModelStore，所以可以看懂这里其实也只是内存级别的，如果Activity因为内存不足而被销毁的状态恢复，是不会保存的。最后我们看下onSaveInstance，还记得我们之前分析创建的时候提到的和状态恢复有挂的逻辑吗。这里再放上代码。
```
private static final Class<?>[] ANDROID_VIEWMODEL_SIGNATURE = new Class[]{Application.class,
            SavedStateHandle.class};
    private static final Class<?>[] VIEWMODEL_SIGNATURE = new Class[]{SavedStateHandle.class};

@NonNull
    @Override
    public <T extends ViewModel> T create(@NonNull String key, @NonNull Class<T> modelClass) {
        boolean isAndroidViewModel = AndroidViewModel.class.isAssignableFrom(modelClass);
        Constructor<T> constructor;
		//是否是ActivityViewModel
        if (isAndroidViewModel && mApplication != null) {
			//通过参数查找构造函数
            constructor = findMatchingConstructor(modelClass, ANDROID_VIEWMODEL_SIGNATURE);
        } else {
            constructor = findMatchingConstructor(modelClass, VIEWMODEL_SIGNATURE);
        }
        // doesn't need SavedStateHandle、
		//没找到直接创建
        if (constructor == null) {
            return mFactory.create(modelClass);
        }
		//这里找到了会传一个SavedStateHandleController到构造函数中
        SavedStateHandleController controller = SavedStateHandleController.create(
                mSavedStateRegistry, mLifecycle, key, mDefaultArgs);
        try {
            T viewmodel;
            if (isAndroidViewModel && mApplication != null) {
                viewmodel = constructor.newInstance(mApplication, controller.getHandle());
            } else {
                viewmodel = constructor.newInstance(controller.getHandle());
            }
            viewmodel.setTagIfAbsent(TAG_SAVED_STATE_HANDLE_CONTROLLER, controller);
            return viewmodel;
        } catch (IllegalAccessException e) {
            throw new RuntimeException("Failed to access " + modelClass, e);
        } catch (InstantiationException e) {
            throw new RuntimeException("A " + modelClass + " cannot be instantiated.", e);
        } catch (InvocationTargetException e) {
            throw new RuntimeException("An exception happened in constructor of "
                    + modelClass, e.getCause());
        }
    }
```
可以看到这里和我们常规的ViewModel的构造函数不同，我们一般的ViewModel都是无参构造函数，或者带一个Application，而这里的ViewModel带来一个`SavedStateHandle`对象，这是我们从来没有使用过的，我们来看一下这个对象。
```
public final class SavedStateHandle {
    final Map<String, Object> mRegular;
    final Map<String, SavedStateProvider> mSavedStateProviders = new HashMap<>();
    private final Map<String, SavingStateLiveData<?>> mLiveDatas = new HashMap<>();

    private static final String VALUES = "values";
    private static final String KEYS = "keys";

    private final SavedStateProvider mSavedStateProvider = new SavedStateProvider() {
        @SuppressWarnings("unchecked")
        @NonNull
        @Override
        public Bundle saveState() {
            // Get the saved state from each SavedStateProvider registered with this
            // SavedStateHandle, iterating through a copy to avoid re-entrance
            Map<String, SavedStateProvider> map = new HashMap<>(mSavedStateProviders);
            for (Map.Entry<String, SavedStateProvider> entry : map.entrySet()) {
                Bundle savedState = entry.getValue().saveState();
                set(entry.getKey(), savedState);
            }
            // Convert the Map of current values into a Bundle
            Set<String> keySet = mRegular.keySet();
            ArrayList keys = new ArrayList(keySet.size());
            ArrayList value = new ArrayList(keys.size());
            for (String key : keySet) {
                keys.add(key);
                value.add(mRegular.get(key));
            }

            Bundle res = new Bundle();
            // "parcelable" arraylists - lol
            res.putParcelableArrayList("keys", keys);
            res.putParcelableArrayList("values", value);
            return res;
        }
    };

public <T> T get(@NonNull String key) {
        return (T) mRegular.get(key);
    }

    /**
     * Associate the given value with the key. The value must have a type that could be stored in
     * {@link android.os.Bundle}
     *
     * @param <T> any type that can be accepted by Bundle.
     */
    @MainThread
    public <T> void set(@NonNull String key, @Nullable T value) {
        validateValue(value);
        @SuppressWarnings("unchecked")
        MutableLiveData<T> mutableLiveData = (MutableLiveData<T>) mLiveDatas.get(key);
        if (mutableLiveData != null) {
            // it will set value;
            mutableLiveData.setValue(value);
        } else {
            mRegular.put(key, value);
        }
    }

 public <T> MutableLiveData<T> getLiveData(@NonNull String key) {
        return getLiveDataInternal(key, false, null);
    }

    @SuppressWarnings("unchecked")
    @NonNull
    private <T> MutableLiveData<T> getLiveDataInternal(
            @NonNull String key,
            boolean hasInitialValue,
            @Nullable T initialValue) {
        MutableLiveData<T> liveData = (MutableLiveData<T>) mLiveDatas.get(key);
        if (liveData != null) {
            return liveData;
        }
        SavingStateLiveData<T> mutableLd;
        // double hashing but null is valid value
        if (mRegular.containsKey(key)) {
            mutableLd = new SavingStateLiveData<>(this, key, (T) mRegular.get(key));
        } else if (hasInitialValue) {
            mutableLd = new SavingStateLiveData<>(this, key, initialValue);
        } else {
            mutableLd = new SavingStateLiveData<>(this, key);
        }
        mLiveDatas.put(key, mutableLd);
        return mutableLd;
    }


static class SavingStateLiveData<T> extends MutableLiveData<T> {
        private String mKey;
        private SavedStateHandle mHandle;

        SavingStateLiveData(SavedStateHandle handle, String key, T value) {
            super(value);
            mKey = key;
            mHandle = handle;
        }

        SavingStateLiveData(SavedStateHandle handle, String key) {
            super();
            mKey = key;
            mHandle = handle;
        }

        @Override
        public void setValue(T value) {
            if (mHandle != null) {
                mHandle.mRegular.put(mKey, value);
            }
            super.setValue(value);
        }

        void detach() {
            mHandle = null;
        }
    }
```
这里只放上我认为的核心代码，其实还是比较简单的，里面有两个Map的数据结构，用于保存变量和LiveData，而对应的SavedStateProvider.saveState方法将两个Map转换成Bundle结构，所以这里我们应该能够感知到既然能够转换成Bundle结构，对应的onSaveInstance就可以存储了。那么我们就看下流程。
```
//ComponentActivity.java
protected void onSaveInstanceState(@NonNull Bundle outState) {
        Lifecycle lifecycle = getLifecycle();
        if (lifecycle instanceof LifecycleRegistry) {
            ((LifecycleRegistry) lifecycle).setCurrentState(Lifecycle.State.CREATED);
        }
        super.onSaveInstanceState(outState);
        mSavedStateRegistryController.performSave(outState);
		//数据存储逻辑
        mActivityResultRegistry.onSaveInstanceState(outState);
    }

//SavedStateRegistry.java
 void performSave(@NonNull Bundle outBundle) {
        Bundle components = new Bundle();
        if (mRestoredState != null) {
            components.putAll(mRestoredState);
        }
		//支持拓展的组件
        for (Iterator<Map.Entry<String, SavedStateProvider>> it =
                mComponents.iteratorWithAdditions(); it.hasNext(); ) {
            Map.Entry<String, SavedStateProvider> entry1 = it.next();
            components.putBundle(entry1.getKey(), entry1.getValue().saveState());
        }
        outBundle.putBundle(SAVED_COMPONENTS_KEY, components);
    }

 @MainThread
    public void registerSavedStateProvider(@NonNull String key,
            @NonNull SavedStateProvider provider) {
        SavedStateProvider previous = mComponents.putIfAbsent(key, provider);
        if (previous != null) {
            throw new IllegalArgumentException("SavedStateProvider with the given key is"
                    + " already registered");
        }
    }
```
可以看到现在Activity把数据恢复的逻辑都抽到了一个`SavedStateRegistry`类中，而这个类利用Components来支持拓展数据恢复，那么我们就看下ViewModel什么时候调用`registerSavedStateProvider`方法，将自己注册到数据恢复的Components中。
```
@NonNull
    @Override
    public <T extends ViewModel> T create(@NonNull String key, @NonNull Class<T> modelClass) {
        boolean isAndroidViewModel = AndroidViewModel.class.isAssignableFrom(modelClass);
        Constructor<T> constructor;
		//...
		//这里找到了会传一个SavedStateHandleController到构造函数中
        SavedStateHandleController controller = SavedStateHandleController.create(
                mSavedStateRegistry, mLifecycle, key, mDefaultArgs);
        try {
            T viewmodel;
            if (isAndroidViewModel && mApplication != null) {
				//传入已经注册的SavedStateHandle
                viewmodel = constructor.newInstance(mApplication, controller.getHandle());
            } else {
                viewmodel = constructor.newInstance(controller.getHandle());
            }
            //....
    }

//SavedStateHandleController.java
static SavedStateHandleController create(SavedStateRegistry registry, Lifecycle lifecycle,
            String key, Bundle defaultArgs) {
        Bundle restoredState = registry.consumeRestoredStateForKey(key);
        SavedStateHandle handle = SavedStateHandle.createHandle(restoredState, defaultArgs);
        SavedStateHandleController controller = new SavedStateHandleController(key, handle);
		//绑定
        controller.attachToLifecycle(registry, lifecycle);
        tryToAddRecreator(registry, lifecycle);
        return controller;
    }

void attachToLifecycle(SavedStateRegistry registry, Lifecycle lifecycle) {
        if (mIsAttached) {
            throw new IllegalStateException("Already attached to lifecycleOwner");
        }
        mIsAttached = true;
        lifecycle.addObserver(this);
		//注册
        registry.registerSavedStateProvider(mKey, mHandle.savedStateProvider());
    }
```
可以看到整个梁璐还是比较短的，我们在创建ViewModel的时候就会把SavedStateHandle注册进去，并且在构造函数的时候传入我们的ViewModel，那么我们在ViewModel中就可以拿到支持状态恢复的SavedStateHandle,我们在需要状态恢复的数据就可以放到SavedStateHandle中，那么这里我们来简单使用下。
```
class SavedStateViewModel(var savedStateHandle: SavedStateHandle) : ViewModel {
    companion object {
        const val KEY_STATE_NAME = "name"
        const val KEY_STATE_LIVE_DATA = "count"
    }

    var name: String = savedStateHandle.get(KEY_STATE_NAME) ?: ""
        set(value) = savedStateHandle.set(KEY_STATE_NAME, value)

    var liveDataCount:MutableLiveData<Int> = savedStateHandle.getLiveData(KEY_STATE_LIVE_DATA)
}	
```
虽然用起来有点别扭，但还是可以接受的，估计Google后续对于这个应该还是会有用法上的优化的。
### 总结
到这里ViewModel的两个特性我们分析完了，看下来其实ViewModel重点还是封装和设计，没有太复杂的技术点，综合前面对于LiveData和Lifecycle的分析，ViewModel更多的是MVVM设计中的逻辑层的容器，如果不是在Android平台涉及View的处理，我们可以理解ViewModel就是一个单纯的java类，用于写Java逻辑，而Android结合Android中的Lifecycle和SaveInstance能力，赋予了这个ViewModel感知生命周期和状态恢复的能力。
#### MVVM感想
在接触MVVM的思想后，我们会发现数据驱动思想的重要性，View层的逻辑单纯就是展示，做到“给我什么展示什么”，逻辑层用于处理逻辑，处理数据，最后再通过数据通信的框架，将我们处理好的数据通知给View展示。这样的数据流转就很直接。
除此之外，我们就应该考虑我们ViewModel的粒度，早起我在接触ViewModel会发现，所有的东西都放在一个ViewModel中，最后的代码也是很混乱的，我会感觉很疑惑，我也是按照MVVM的思想来实现的，难道这套框架并不足以承载太过于复杂的场景吗？后面逐渐发现，我们需要考虑粒度的划分，重点是两个：
* 1.LiveData的收敛，避免LiveData爆炸
* 2.ViewModel的粒度，单一职责，抽取ViewModel

结合上面两点，我们才能够充分发挥MVVM的优势，首先LiveData的收敛，不要什么状态都新建一个LiveData，我们应该考虑LiveData能否整合，保证View层的监听LiveData的出口够小。然后就是ViewModel的抽取，单一职责，最理想的状态时ViewModel的复用，当一个ViewModel内部的逻辑是闭合的，这个ViewModel就不再是只服务于这一个Activity，而是一个业务，只要用到这个业务的Activity都可以使用这个ViewModel。
