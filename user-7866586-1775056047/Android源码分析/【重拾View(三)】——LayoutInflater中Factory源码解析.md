>1.[【重拾View(一)】——setContentView()源码解析](https://www.jianshu.com/p/9e1cf127f0ae)
>2.[【重拾View(二)】——LayoutInflater源码解析](https://www.jianshu.com/p/86696bda40f3)
>3.[【重拾View(三)】——LayoutInflater中Factory源码解析](https://www.jianshu.com/p/281d87f17c66)
### 前言
上一篇博客分析了LayoutInflater的inflate方法，可以说对inflate已经有了一个比较全面的认识，这里专门抽出一片博客专门分析一下LayoutInflater中的Factory相关的源码解析，因为这算是Google处理解析的一个小插曲，利用这个Factory我们可以完成很多自定义解析方式，有很多框架实质都是基于这个原理。

### 源码解析
```
View createViewFromTag(View parent, String name, Context context, AttributeSet attrs,
            boolean ignoreThemeAttr) {
        ...

        try {
            View view;
            if (mFactory2 != null) {
                view = mFactory2.onCreateView(parent, name, context, attrs);
            } else if (mFactory != null) {
                view = mFactory.onCreateView(name, context, attrs);
            } else {
                view = null;
            }

            if (view == null && mPrivateFactory != null) {
                view = mPrivateFactory.onCreateView(parent, name, context, attrs);
            }

            if (view == null) {
                final Object lastContext = mConstructorArgs[0];
                mConstructorArgs[0] = context;
                try {
                    if (-1 == name.indexOf('.')) {
                        view = onCreateView(parent, name, attrs);
                    } else {
                        view = createView(name, null, attrs);
                    }
                } finally {
                    mConstructorArgs[0] = lastContext;
                }
            }

            return view;
        }
...
```
这里放上了上一篇博客分析的解析创建View的关键方法`createViewFromTag`，可以看到在创建的一开始，首先有三处判断条件，分辨判断了`mFactory2`，`mFactory`，`mPrivateFactory`的`onCreateView`方法来创建View。如果这三个创建出的View！=null ,则直接返回了这个View.
这里其实三个都是LayoutInflater的成员变量，都有对应的`set`和`get`方法。所以这里我们关注一下这三个的定义。

```
private Factory mFactory;
    private Factory2 mFactory2;
    private Factory2 mPrivateFactory;

public interface Factory {
        public View onCreateView(String name, Context context, AttributeSet attrs);
    }

public interface Factory2 extends Factory {
        public View onCreateView(View parent, String name, Context context, AttributeSet attrs);
    }
```
其实可以看到就是简单的两个接口，并且`Factory2`继承了Factory。其实两者也有一定的区别：
* 1. LayoutInflater.Factory2 是API 11 被加进来的；
* 2. 可以对创建 View 的 Parent 进行控制,方法参数中多了`parent`；

为什么说是是API 11 被加进来的呢？既然说到了API11，那么我们来看一下API11对应的`AppCompatActivity `的源码
### AppCompatActivity源码分析
```
public class AppCompatActivity extends FragmentActivity implements AppCompatCallback, SupportParentable, DelegateProvider {
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        AppCompatDelegate delegate = this.getDelegate();、
		//设置Factory工厂
        delegate.installViewFactory();
        delegate.onCreate(savedInstanceState);
        if(delegate.applyDayNight() && this.mThemeId != 0) {
            if(VERSION.SDK_INT >= 23) {
                this.onApplyThemeResource(this.getTheme(), this.mThemeId, false);
            } else {
                this.setTheme(this.mThemeId);
            }
        }

        super.onCreate(savedInstanceState);
    }
```
这里可以看到，在`AppCompatActivity`的`onCreate`方法中，调用了` delegate.installViewFactory();`方法，这里就利用`LayoutInflater`的Factory进行了设置。
```
public static AppCompatDelegate create(Activity activity, AppCompatCallback callback) {
        return create(activity, activity.getWindow(), callback);
    }

private static AppCompatDelegate create(Context context, Window window, AppCompatCallback callback) {
        return (AppCompatDelegate)(VERSION.SDK_INT >= 24?new AppCompatDelegateImplN(context, window, callback):(VERSION.SDK_INT >= 23?new AppCompatDelegateImplV23(context, window, callback):(VERSION.SDK_INT >= 14?new AppCompatDelegateImplV14(context, window, callback):(VERSION.SDK_INT >= 11?new AppCompatDelegateImplV11(context, window, callback):new AppCompatDelegateImplV9(context, window, callback)))));
    }
```
关于`AppCompatDelegate`可以看到就是不同的版本判断得到不同的类，经常看源码的应该都清楚，这里一般不同版本都是**继承**关系，所以这里我们就来看一下`AppCompatDelegateImplV9`，不出意外`installViewFactory`方法在这里面就有定义。
```
class AppCompatDelegateImplV9 extends AppCompatDelegateImplBase implements Callback, Factory2 {
public void installViewFactory() {
        LayoutInflater layoutInflater = LayoutInflater.from(this.mContext);
        if(layoutInflater.getFactory() == null) {
            LayoutInflaterCompat.setFactory2(layoutInflater, this);
        } else if(!(layoutInflater.getFactory2() instanceof AppCompatDelegateImplV9)) {
            Log.i("AppCompatDelegate", "The Activity's LayoutInflater already has a Factory installed so we can not install AppCompat's");
        }
    }

public final View onCreateView(View parent, String name, Context context, AttributeSet attrs) {
        View view = this.callActivityOnCreateView(parent, name, context, attrs);
        return view != null?view:this.createView(parent, name, context, attrs);
    }

public View createView(View parent, String name, @NonNull Context context, @NonNull AttributeSet attrs) {
        if(this.mAppCompatViewInflater == null) {
            this.mAppCompatViewInflater = new AppCompatViewInflater();
        }

        boolean inheritContext = false;
        if(IS_PRE_LOLLIPOP) {
            inheritContext = attrs instanceof XmlPullParser?((XmlPullParser)attrs).getDepth() > 1:this.shouldInheritContext((ViewParent)parent);
        }

        return this.mAppCompatViewInflater.createView(parent, name, context, attrs, inheritContext, IS_PRE_LOLLIPOP, true, VectorEnabledTintResources.shouldBeUsed());
    }
}
```
可以看到果不其然，这里利用`LayoutInflater`设置了一个`Factory`、可以看到最终会调用`createView`方法，并且创建了一个`AppCompatViewInflater`，并调用了其`createView`方法。
```
public final View createView(View parent, String name, @NonNull Context context, @NonNull AttributeSet attrs, boolean inheritContext, boolean readAndroidTheme, boolean readAppTheme, boolean wrapContext) {
        if(inheritContext && parent != null) {
            context = parent.getContext();
        }

        if(readAndroidTheme || readAppTheme) {
            context = themifyContext(context, attrs, readAndroidTheme, readAppTheme);
        }

        if(wrapContext) {
            context = TintContextWrapper.wrap(context);
        }

        View view = null;
        byte var12 = -1;
        switch(name.hashCode()) {
        case -1946472170:
            if(name.equals("RatingBar")) {
                var12 = 11;
            }
            break;
        case -1455429095:
            if(name.equals("CheckedTextView")) {
                var12 = 8;
            }
            break;
        case -1346021293:
            if(name.equals("MultiAutoCompleteTextView")) {
                var12 = 10;
            }
            break;
        case -938935918:
            if(name.equals("TextView")) {
                var12 = 0;
            }
            break;
        case -937446323:
            if(name.equals("ImageButton")) {
                var12 = 5;
            }
            break;
        case -658531749:
            if(name.equals("SeekBar")) {
                var12 = 12;
            }
            break;
        case -339785223:
            if(name.equals("Spinner")) {
                var12 = 4;
            }
            break;
        case 776382189:
            if(name.equals("RadioButton")) {
                var12 = 7;
            }
            break;
        case 1125864064:
            if(name.equals("ImageView")) {
                var12 = 1;
            }
            break;
        case 1413872058:
            if(name.equals("AutoCompleteTextView")) {
                var12 = 9;
            }
            break;
        case 1601505219:
            if(name.equals("CheckBox")) {
                var12 = 6;
            }
            break;
        case 1666676343:
            if(name.equals("EditText")) {
                var12 = 3;
            }
            break;
        case 2001146706:
            if(name.equals("Button")) {
                var12 = 2;
            }
        }

        switch(var12) {
        case 0:
            view = new AppCompatTextView(context, attrs);
            break;
        case 1:
            view = new AppCompatImageView(context, attrs);
            break;
        case 2:
            view = new AppCompatButton(context, attrs);
            break;
        case 3:
            view = new AppCompatEditText(context, attrs);
            break;
        case 4:
            view = new AppCompatSpinner(context, attrs);
            break;
        case 5:
            view = new AppCompatImageButton(context, attrs);
            break;
        case 6:
            view = new AppCompatCheckBox(context, attrs);
            break;
        case 7:
            view = new AppCompatRadioButton(context, attrs);
            break;
        case 8:
            view = new AppCompatCheckedTextView(context, attrs);
            break;
        case 9:
            view = new AppCompatAutoCompleteTextView(context, attrs);
            break;
        case 10:
            view = new AppCompatMultiAutoCompleteTextView(context, attrs);
            break;
        case 11:
            view = new AppCompatRatingBar(context, attrs);
            break;
        case 12:
            view = new AppCompatSeekBar(context, attrs);
        }

        if(view == null && context != context) {
            view = this.createViewFromTag(context, name, attrs);
        }

        if(view != null) {
            this.checkOnClickListener((View)view, attrs);
        }

        return (View)view;
    }
```
会发现这里将其实就是将一些低版本的Widget自动变成兼容的Widget（例如将 TextView 变成 AppCompatTextView）以便于向下兼容新版本中的效果，在高版本中的一些Widget新特性就是这样在老版本中也能展示的。
综上，我们完全也可以仿照这种实现方式，将我们需要转变的View转换成我们自定义的View。但是这里我们需要注意一点。
```
public void setFactory2(Factory2 factory) {
		//如果设置过，再设置会抛异常
        if (mFactorySet) {
            throw new IllegalStateException("A factory has already been set on this LayoutInflater");
        }
        if (factory == null) {
            throw new NullPointerException("Given factory can not be null");
        }
		//一旦设置过，就会置true
        mFactorySet = true;
        if (mFactory == null) {
            mFactory = mFactory2 = factory;
        } else {
            mFactory = mFactory2 = new FactoryMerger(factory, factory, mFactory, mFactory2);
        }
    }
```
可以看到这里的`set`方法，原则上是只允许设置一次的，设置过后，就会将`mFactorySet`变量设置为true,如果再次设置就会抛异常。所以这里当我们的Activity继承的是刚才提到的`AppCompatActivity`。通过刚才的源码我们发现，在`AppCompatActivity`的onCreate方法里源码会自动设置一个Factory用于替换Widget向下兼容。所以当我们这时需要自己定义Factory的时候，我们就需要注意需**要在`super.onCreate()`方法之前设置，不然会报异常（反射想干啥干啥...）**
### FragmentActivity的源码解析
这里还要分析一下`FragmentActivity`，使用过`Fragment`的都知道，我们需要将Activity继承`FragmentActivity`，这是为什么呢？待我们来慢慢分析。
```
<fragment
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    />
```
首先我们知道，`Fragment`是可以使用标签在XML中定义的，所以我们可以从这个角度考虑一下，看过上一篇博客的应该清楚，在解析XML的时候，特殊的标签都会有专门的条件判断进行解析，例如`merge`，但是却没有`Fragment`标签，结合前面的分析，我们这时候应该就该明白，其实也是这个Factory捣的鬼，所以对应于需要继承`FragmentActivity`，我们这时候就需要去看一下`FragmentActivity`的源码。通过继承关系我们会发现最终在父类`Activity`实现了`Factory2`接口。
![继承关系](https://upload-images.jianshu.io/upload_images/7866586-8883b5bad2ddbe89.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

```
final FragmentController mFragments = FragmentController.createController(new HostCallbacks());

@Nullable
    public View onCreateView(String name, Context context, AttributeSet attrs) {
        return null;
    }
    public View onCreateView(View parent, String name, Context context, AttributeSet attrs) {
        if (!"fragment".equals(name)) {
            return onCreateView(name, context, attrs);
        }

        return mFragments.onCreateView(parent, name, context, attrs);
    }
```
可以看到这里对`fragment`进行了特殊的判断，当时`Fragment`标签时，会交给`FragmentController`进行创建，而这个`FragmentController`可以看到在声明变量的时候已经创建了。
```
private FragmentController(FragmentHostCallback<?> callbacks) {
        mHost = callbacks;
    }

public View onCreateView(View parent, String name, Context context, AttributeSet attrs) {
        return mHost.mFragmentManager.onCreateView(parent, name, context, attrs);
    }
```
而且可以看到这里最终会交给一个叫`mFragmentManager`的onCreateView方法，这里其实已经很熟悉了，但是我们还是来看一看，可以看到这里`mHost`变量是在构造函数的时候传入的，而前面构造函数可以看到直接new了一个`HostCallbacks()`，而`HostCallbacks`是Activity的内部类，继承于`FragmentHostCallback`。
```
public abstract class FragmentHostCallback<E> extends FragmentContainer {
...
    final FragmentManagerImpl mFragmentManager = new FragmentManagerImpl();

inal class FragmentManagerImpl extends FragmentManager implements LayoutInflater.Factory2 {
@Override
    public View onCreateView(View parent, String name, Context context, AttributeSet attrs) {
        if (!"fragment".equals(name)) {
            return null;
        }

        String fname = attrs.getAttributeValue(null, "class");
        TypedArray a =
                context.obtainStyledAttributes(attrs, com.android.internal.R.styleable.Fragment);
        if (fname == null) {
            fname = a.getString(com.android.internal.R.styleable.Fragment_name);
        }
        int id = a.getResourceId(com.android.internal.R.styleable.Fragment_id, View.NO_ID);
        String tag = a.getString(com.android.internal.R.styleable.Fragment_tag);
        a.recycle();

        int containerId = parent != null ? parent.getId() : 0;
        if (containerId == View.NO_ID && id == View.NO_ID && tag == null) {
            throw new IllegalArgumentException(attrs.getPositionDescription()
                    + ": Must specify unique android:id, android:tag, or have a parent with"
                    + " an id for " + fname);
        }

        // If we restored from a previous state, we may already have
        // instantiated this fragment from the state and should use
        // that instance instead of making a new one.
		//先查找已存在的Fragment
        Fragment fragment = id != View.NO_ID ? findFragmentById(id) : null;
        if (fragment == null && tag != null) {
            fragment = findFragmentByTag(tag);
        }
        if (fragment == null && containerId != View.NO_ID) {
            fragment = findFragmentById(containerId);
        }

        if (FragmentManagerImpl.DEBUG) Log.v(TAG, "onCreateView: id=0x"
                + Integer.toHexString(id) + " fname=" + fname
                + " existing=" + fragment);
        if (fragment == null) {
			//反射创建
            fragment = mContainer.instantiate(context, fname, null);
            fragment.mFromLayout = true;
            fragment.mFragmentId = id != 0 ? id : containerId;
            fragment.mContainerId = containerId;
            fragment.mTag = tag;
            fragment.mInLayout = true;
            fragment.mFragmentManager = this;
            fragment.mHost = mHost;
            fragment.onInflate(mHost.getContext(), attrs, fragment.mSavedFragmentState);
            addFragment(fragment, true);
        } else if (fragment.mInLayout) {
            // A fragment already exists and it is not one we restored from
            // previous state.
            throw new IllegalArgumentException(attrs.getPositionDescription()
                    + ": Duplicate id 0x" + Integer.toHexString(id)
                    + ", tag " + tag + ", or parent id 0x" + Integer.toHexString(containerId)
                    + " with another fragment for " + fname);
        } else {
            // This fragment was retained from a previous instance; get it
            // going now.
            fragment.mInLayout = true;
            fragment.mHost = mHost;
            // If this fragment is newly instantiated (either right now, or
            // from last saved state), then give it the attributes to
            // initialize itself.
            if (!fragment.mRetaining) {
                fragment.onInflate(mHost.getContext(), attrs, fragment.mSavedFragmentState);
            }
        }

        // If we haven't finished entering the CREATED state ourselves yet,
        // push the inflated child fragment along. This will ensureInflatedFragmentView
        // at the right phase of the lifecycle so that we will have mView populated
        // for compliant fragments below.
        if (mCurState < Fragment.CREATED && fragment.mFromLayout) {
			//回调Fragment的onCreateView生命周期
            moveToState(fragment, Fragment.CREATED, 0, 0, false);
        } else {
            moveToState(fragment);
        }

        if (fragment.mView == null) {
            throw new IllegalStateException("Fragment " + fname
                    + " did not create a view.");
        }
        if (id != 0) {
            fragment.mView.setId(id);
        }
        if (fragment.mView.getTag() == null) {
            fragment.mView.setTag(tag);
        }
        return fragment.mView;
    }
}
}
```
到这里就很清楚了，这里首先查找已存在的Fragment，如果没有找到就利用**反射**创建`Fragment`的实例。
```
void moveToState(Fragment f, int newState, int transit, int transitionStyle,
            boolean keepActive) {
	switch (f.mState) {
		 case Fragment.CREATED:
			f.mView = f.performCreateView(f.performGetLayoutInflater(
                                    f.mSavedFragmentState), container, f.mSavedFragmentState);
...
	}
}

public class Fragment implements Parcelable{
	View performCreateView(LayoutInflater inflater, ViewGroup container,
            Bundle savedInstanceState) {
        if (mChildFragmentManager != null) {
            mChildFragmentManager.noteStateNotSaved();
        }
        mPerformedCreateView = true;
		//回调生命周期
        return onCreateView(inflater, container, savedInstanceState);
    }
}
```

### 总结
通过上面的分析我们其实会发现Factory的强大之处，利用Factory我们可以做许多的操作，例如更换主题等。经过这两篇博客的分析，对于LayoutInflater我们算是有了一个比较全面的了解，只能说对于View，我们需要了解的还有很多。

### 相关博客推荐
[LayoutInflater 源码分析系列](http://yifeiyuan.me/2017/01/02/analyze-layoutinflater1-inflate/)

[LayoutInflater的源码分析和拓展](https://www.jianshu.com/p/f0f3de2f63e3)
