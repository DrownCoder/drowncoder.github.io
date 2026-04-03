---
title: "【Window系列】——PopupWindow的前世今生"
category: "Android源码分析"
category_slug: "android源码分析"
source_name: "【Window系列】——PopupWindow的前世今生"
sort_key: 0052
---
>本系列博客基于android-28版本
[【Window系列】——Toast源码解析](https://www.jianshu.com/p/f9e60e9272cf)
[【Window系列】——PopupWindow的前世今生](https://www.jianshu.com/p/9dafea9cb3c0)
[【Window系列】——Dialog源码解析](https://www.jianshu.com/p/7874bfb20ca0)
[【Window系列】——Window中的Token](https://www.jianshu.com/p/3411ee4cb739)
### 前言
上一篇博客分析了Toast的源码，一提到Window必然少不了本篇博客分析的`PopupWindow`，本来我以为是一样的流程，创建Window，设置View到DecorView，加入Window，完事儿...但却发现`PopupWindow`却没有按照这种实现方式实现的。
### 大纲
本篇博客会分析一下几点：
>1. PopupWindow的实现原理源码
>2. PopupWindow关于BackgroundDrawable的版本差异导致的问题
>3. PopupWindow的触摸事件处理
### 源码分析
我们平时使用`PopupWindow`主要涉及以下三个核心方法：
```
PopupWindow window = new PopupWindow();
window.setContentView(...);
window.showAsDropDown(...);
```
所以首先看一下构造函数
```
public PopupWindow(View contentView, int width, int height, boolean focusable) {
        if (contentView != null) {
            mContext = contentView.getContext();
            mWindowManager = (WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE);
        }

        setContentView(contentView);
        setWidth(width);
        setHeight(height);
        setFocusable(focusable);
    }
```
如果在构造函数设置了`ContentView`，那么直接获取`Context`对象和`WindowManager`，调用`setContentView`方法，设置宽高，和`Focusable`,这里要注意一下`Focusable`这个变量，后面会讲到这个变量在`PopupWindow`中的作用。
如果我们调用的是最基础的构造函数，一般我们下一步会调用`setContentView`方法设置我们的布局，那么这里我们就来看一下这个方法。
```
public void setContentView(View contentView) {
        if (isShowing()) {
            return;
        }
        //保存ContentView
        mContentView = contentView;

        if (mContext == null && mContentView != null) {
            mContext = mContentView.getContext();
        }

        if (mWindowManager == null && mContentView != null) {
            mWindowManager = (WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE);
        }

        // Setting the default for attachedInDecor based on SDK version here
        // instead of in the constructor since we might not have the context
        // object in the constructor. We only want to set default here if the
        // app hasn't already set the attachedInDecor.
        if (mContext != null && !mAttachedInDecorSet) {
            // Attach popup window in decor frame of parent window by default for
            // {@link Build.VERSION_CODES.LOLLIPOP_MR1} or greater. Keep current
            // behavior of not attaching to decor frame for older SDKs.
            setAttachedInDecor(mContext.getApplicationInfo().targetSdkVersion
                    >= Build.VERSION_CODES.LOLLIPOP_MR1);
        }

    }
```
可以看到，和刚才看到的构造函数基本相同，保存了`ContentView`变量后，获取`Context`和`WindowManger`对象。
可以看到上面两个步骤基本上都是做的准备工作，那么接下来看一下最核心的展示方法`showAsDropDown`
```
public void showAsDropDown(View anchor) {
        showAsDropDown(anchor, 0, 0);
    }
    
public void showAsDropDown(View anchor, int xoff, int yoff, int gravity) {
        if (isShowing() || !hasContentView()) {
            return;
        }

        TransitionManager.endTransitions(mDecorView);
        //绑定监听，设置变量
        attachToAnchor(anchor, xoff, yoff, gravity);

        mIsShowing = true;
        mIsDropdown = true;
        //创建布局参数
        final WindowManager.LayoutParams p =
                createPopupLayoutParams(anchor.getApplicationWindowToken());
        //包裹布局，构建布局层级
        preparePopup(p);

        final boolean aboveAnchor = findDropDownPosition(anchor, p, xoff, yoff,
                p.width, p.height, gravity, mAllowScrollingAnchorParent);
        updateAboveAnchor(aboveAnchor);
        p.accessibilityIdOfAnchor = (anchor != null) ? anchor.getAccessibilityViewId() : -1;
        //添加布局到Window中
        invokePopup(p);
    }
```
可以看到，这个方法其实还是利用了重载，实现了很多方法，最终都是到了最后这个方法里。
上面大概分了四部分，我分别写了注释，这里来单独看一下。
```
protected void attachToAnchor(View anchor, int xoff, int yoff, int gravity) {
        detachFromAnchor();

        final ViewTreeObserver vto = anchor.getViewTreeObserver();
        if (vto != null) {
            vto.addOnScrollChangedListener(mOnScrollChangedListener);
        }
        anchor.addOnAttachStateChangeListener(mOnAnchorDetachedListener);

        final View anchorRoot = anchor.getRootView();
        anchorRoot.addOnAttachStateChangeListener(mOnAnchorRootDetachedListener);
        anchorRoot.addOnLayoutChangeListener(mOnLayoutChangeListener);
        //弱引用
        mAnchor = new WeakReference<>(anchor);
        mAnchorRoot = new WeakReference<>(anchorRoot);
        mIsAnchorRootAttached = anchorRoot.isAttachedToWindow();
        mParentRootView = mAnchorRoot;

        mAnchorXoff = xoff;
        mAnchorYoff = yoff;
        mAnchoredGravity = gravity;
    }
```
可以看到这个方法主要是设置我们传入到参数的，但是这里要注意的是Google在这里使用了**弱引用**，这个我感觉是比较少见的，目前我所了解的FrameWork层的源码里，很少看到Google使用**弱引用**，这里利用**弱引用**保存了传入的布局和顶层父布局。
```
protected final WindowManager.LayoutParams createPopupLayoutParams(IBinder token) {
        final WindowManager.LayoutParams p = new WindowManager.LayoutParams();

        // These gravity settings put the view at the top left corner of the
        // screen. The view is then positioned to the appropriate location by
        // setting the x and y offsets to match the anchor's bottom-left
        // corner.
        p.gravity = computeGravity();
        p.flags = computeFlags(p.flags);
        p.type = mWindowLayoutType;
        //设置Token
        p.token = token;
        p.softInputMode = mSoftInputMode;
        //设置动画
        p.windowAnimations = computeAnimationResource();

        if (mBackground != null) {
            p.format = mBackground.getOpacity();
        } else {
            p.format = PixelFormat.TRANSLUCENT;
        }
        //设置宽高
        if (mHeightMode < 0) {
            p.height = mLastHeight = mHeightMode;
        } else {
            p.height = mLastHeight = mHeight;
        }

        if (mWidthMode < 0) {
            p.width = mLastWidth = mWidthMode;
        } else {
            p.width = mLastWidth = mWidth;
        }

        p.privateFlags = PRIVATE_FLAG_WILL_NOT_REPLACE_ON_RELAUNCH
                | PRIVATE_FLAG_LAYOUT_CHILD_WINDOW_IN_PARENT_FRAME;

        // Used for debugging.
        p.setTitle("PopupWindow:" + Integer.toHexString(hashCode()));

        return p;
    }
```
`createPopupLayoutParams`是用来创建一个`LayoutParam`，这里注重注意一下`token`这个变量，看过前一篇博客的应该都记得，`Toast`组件也需要一个`token`变量，这里这个`token`可以看到是用`anchor.getApplicationWindowToken()`获取的，也就是父布局的`token`。关于`token`后面会抽出一篇博客来专门分析一下，`token`对于Window类型的影响。
```
private void preparePopup(WindowManager.LayoutParams p) {
        if (mContentView == null || mContext == null || mWindowManager == null) {
            throw new IllegalStateException("You must specify a valid content view by "
                    + "calling setContentView() before attempting to show the popup.");
        }

        if (p.accessibilityTitle == null) {
            p.accessibilityTitle = mContext.getString(R.string.popup_window_default_title);
        }

        // The old decor view may be transitioning out. Make sure it finishes
        // and cleans up before we try to create another one.
        if (mDecorView != null) {
            mDecorView.cancelTransitions();
        }

        // When a background is available, we embed the content view within
        // another view that owns the background drawable.
        //设置Background包裹
        if (mBackground != null) {
            mBackgroundView = createBackgroundView(mContentView);
            mBackgroundView.setBackground(mBackground);
        } else {
            mBackgroundView = mContentView;
        }
        //再用DecorView包裹
        mDecorView = createDecorView(mBackgroundView);
        mDecorView.setIsRootNamespace(true);
        //设置elevation
        // The background owner should be elevated so that it casts a shadow.
        mBackgroundView.setElevation(mElevation);

        // We may wrap that in another view, so we'll need to manually specify
        // the surface insets.
        p.setSurfaceInsets(mBackgroundView, true /*manual*/, true /*preservePrevious*/);

        mPopupViewInitialLayoutDirectionInherited =
                (mContentView.getRawLayoutDirection() == View.LAYOUT_DIRECTION_INHERIT);
    }
```
这个方法可以说是`popupwindow`的最核心的方法了，首先我们可以看到，对`mBackgroud`变量进行了判空，如果设置了`backgroud`，则执行`createBackgroundView`方法。
```
private PopupBackgroundView createBackgroundView(View contentView) {
        final ViewGroup.LayoutParams layoutParams = mContentView.getLayoutParams();
        final int height;
        if (layoutParams != null && layoutParams.height == WRAP_CONTENT) {
            height = WRAP_CONTENT;
        } else {
            height = MATCH_PARENT;
        }

        final PopupBackgroundView backgroundView = new PopupBackgroundView(mContext);
        final PopupBackgroundView.LayoutParams listParams = new PopupBackgroundView.LayoutParams(
                MATCH_PARENT, height);
        backgroundView.addView(contentView, listParams);

        return backgroundView;
    }
```
这里可以看到，构建了一个宽高相同的布局参数，并且创建了一个`PopupBackgroundView`，利用`addView`方法，将我们的`ContentView`包裹了起来。
```
private class PopupBackgroundView extends FrameLayout {
        public PopupBackgroundView(Context context) {
            super(context);
        }

        @Override
        protected int[] onCreateDrawableState(int extraSpace) {
            if (mAboveAnchor) {
                final int[] drawableState = super.onCreateDrawableState(extraSpace + 1);
                View.mergeDrawableStates(drawableState, ABOVE_ANCHOR_STATE_SET);
                return drawableState;
            } else {
                return super.onCreateDrawableState(extraSpace);
            }
        }
    }
```
这里的`PopupBackgroundView`其实就是一个`FrameLayout`，单纯的只是为了设置`Backgroud`。
接下来执行`createDecorView `方法。
```
private PopupDecorView createDecorView(View contentView) {
        final ViewGroup.LayoutParams layoutParams = mContentView.getLayoutParams();
        final int height;
        if (layoutParams != null && layoutParams.height == WRAP_CONTENT) {
            height = WRAP_CONTENT;
        } else {
            height = MATCH_PARENT;
        }

        final PopupDecorView decorView = new PopupDecorView(mContext);
        decorView.addView(contentView, MATCH_PARENT, height);
        decorView.setClipChildren(false);
        decorView.setClipToPadding(false);

        return decorView;
    }
```
可以看到和刚才大同小异，哪这回为什么又要包裹一层呢？这里就要看一下`PopupDecorView`
```
private class PopupDecorView extends FrameLayout {
        /** Runnable used to clean up listeners after exit transition. */
        private Runnable mCleanupAfterExit;

        public PopupDecorView(Context context) {
            super(context);
        }

        @Override
        public boolean dispatchKeyEvent(KeyEvent event) {
        		//对返回键做了特殊处理
            if (event.getKeyCode() == KeyEvent.KEYCODE_BACK) {
                if (getKeyDispatcherState() == null) {
                    return super.dispatchKeyEvent(event);
                }

                if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
                    final KeyEvent.DispatcherState state = getKeyDispatcherState();
                    if (state != null) {
                        state.startTracking(event, this);
                    }
                    return true;
                } else if (event.getAction() == KeyEvent.ACTION_UP) {
                    final KeyEvent.DispatcherState state = getKeyDispatcherState();
                    if (state != null && state.isTracking(event) && !event.isCanceled()) {
                        dismiss();
                        return true;
                    }
                }
                return super.dispatchKeyEvent(event);
            } else {
                return super.dispatchKeyEvent(event);
            }
        }

        @Override
        public boolean dispatchTouchEvent(MotionEvent ev) {
            if (mTouchInterceptor != null && mTouchInterceptor.onTouch(this, ev)) {
                return true;
            }
            return super.dispatchTouchEvent(ev);
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            final int x = (int) event.getX();
            final int y = (int) event.getY();

            if ((event.getAction() == MotionEvent.ACTION_DOWN)
                    && ((x < 0) || (x >= getWidth()) || (y < 0) || (y >= getHeight()))) {
                //触摸位置在外部，则直接dismiss()
                dismiss();
                return true;
            } else if (event.getAction() == MotionEvent.ACTION_OUTSIDE) {
                dismiss();
                return true;
            } else {
                return super.onTouchEvent(event);
            }
        }
...
} 
```
这里就内容很多了，首先这个还是一个继承了`FrameLayout`的布局，唯一不同的是，这里重写了两个关键方法`dispatchKeyEvent `和`onTouchEvent `，所以我们应该知道这里对键盘事件和触摸事件做了特殊处理，当是返回键时或者触摸位置在View的外部的时候则调用`dismiss()`方法。
**这也就是为什么Popupwindow点击外部可以消失的原因，也就是触摸事件处理**。
这里还有一个地方值得我们注意
```
@Override
        public boolean dispatchTouchEvent(MotionEvent ev) {
            if (mTouchInterceptor != null && mTouchInterceptor.onTouch(this, ev)) {
                return true;
            }
            return super.dispatchTouchEvent(ev);
        }
```
可以看到这里还重写了`dispatchTouchEvent`方法，熟悉**Android事件分发流程**的应该清楚，这里是事件分发的顶层，这里多出了一个`mTouchInterceptor`这个概念，其实就是一个**拦截器**，也就是说，对于`PopupWindow`，我们是可以自定义事件的处理的。
做完这所有的准备后，就是最后一个方法了。
```
private void invokePopup(WindowManager.LayoutParams p) {
        if (mContext != null) {
            p.packageName = mContext.getPackageName();
        }

        final PopupDecorView decorView = mDecorView;
        decorView.setFitsSystemWindows(mLayoutInsetDecor);

        setLayoutDirectionFromAnchor();
        //通过WindowManger加入View
        mWindowManager.addView(decorView, p);

        if (mEnterTransition != null) {
            decorView.requestEnterTransition(mEnterTransition);
        }
    }
```
终于看到了最核心的显示方法，我们可以确定`PopupWindow`是通过`WindowManger`的`addView`方法加入的。可以发现，**其实PopupWindow并没有重新创建新的Window,而是在当前Window上，利用`WindowManger.addView`加入的。**，这可以说就是`PopupWindow`的显示原理。
### PopupWindow关于BackgroundDrawable的版本差异导致的问题
最开始学习`PopupWindow`的使用方法的时候，我们经常会看到这样的一个注释。
```
// 如果不设置PopupWindow的背景,就会出现一个问题：无论是点击外部区域还是Back键都无法dismiss弹框
popupWindow.setBackgroundDrawable(new ColorDrawable());
```
通过上面的源码分析，我们本没有发现`BackgroundDrawable`会有这么大的影响，只是单纯的印象一个包装View的背景，这里就要说一下`PopupWindow`的版本差异了，本篇博客是基于`android-28`,通过源码我们能知道`backgrounddrawable`不会有这样的影响。但是我们来看一下`Android4.2.2`的源码
```
private void preparePopup(WindowManager.LayoutParams p) {
        if (mContentView == null || mContext == null || mWindowManager == null) {
            throw new IllegalStateException("You must specify a valid content view by "
                    + "calling setContentView() before attempting to show the popup.");
        }

        if (mBackground != null) {
            final ViewGroup.LayoutParams layoutParams = mContentView.getLayoutParams();
            int height = ViewGroup.LayoutParams.MATCH_PARENT;
            if (layoutParams != null &&
                    layoutParams.height == ViewGroup.LayoutParams.WRAP_CONTENT) {
                height = ViewGroup.LayoutParams.WRAP_CONTENT;
            }

            // when a background is available, we embed the content view
            // within another view that owns the background drawable
            PopupViewContainer popupViewContainer = new PopupViewContainer(mContext);
            PopupViewContainer.LayoutParams listParams = new PopupViewContainer.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, height
            );
            popupViewContainer.setBackgroundDrawable(mBackground);
            popupViewContainer.addView(mContentView, listParams);

            mPopupView = popupViewContainer;
        } else {
            mPopupView = mContentView;
        }
        mPopupViewInitialLayoutDirectionInherited =
                (mPopupView.getRawLayoutDirection() == View.LAYOUT_DIRECTION_INHERIT);
        mPopupWidth = p.width;
        mPopupHeight = p.height;
    }
```
可以看到这里在`preparePopup`方法里，就有了不同，这里如果设置了`mBackground `就会使用`PopupViewContainer `保存。
```
private class PopupViewContainer extends FrameLayout {
1542        private static final String TAG = "PopupWindow.PopupViewContainer";
1543
1544        public PopupViewContainer(Context context) {
1545            super(context);
1546        }
1547
1548        @Override
1549        protected int[] onCreateDrawableState(int extraSpace) {
1550            if (mAboveAnchor) {
1551                // 1 more needed for the above anchor state
1552                final int[] drawableState = super.onCreateDrawableState(extraSpace + 1);
1553                View.mergeDrawableStates(drawableState, ABOVE_ANCHOR_STATE_SET);
1554                return drawableState;
1555            } else {
1556                return super.onCreateDrawableState(extraSpace);
1557            }
1558        }
1559
1560        @Override
1561        public boolean dispatchKeyEvent(KeyEvent event) {
1562            if (event.getKeyCode() == KeyEvent.KEYCODE_BACK) {
1563                if (getKeyDispatcherState() == null) {
1564                    return super.dispatchKeyEvent(event);
1565                }
1566
1567                if (event.getAction() == KeyEvent.ACTION_DOWN
1568                        && event.getRepeatCount() == 0) {
1569                    KeyEvent.DispatcherState state = getKeyDispatcherState();
1570                    if (state != null) {
1571                        state.startTracking(event, this);
1572                    }
1573                    return true;
1574                } else if (event.getAction() == KeyEvent.ACTION_UP) {
1575                    KeyEvent.DispatcherState state = getKeyDispatcherState();
1576                    if (state != null && state.isTracking(event) && !event.isCanceled()) {
1577                        dismiss();
1578                        return true;
1579                    }
1580                }
1581                return super.dispatchKeyEvent(event);
1582            } else {
1583                return super.dispatchKeyEvent(event);
1584            }
1585        }
1586
1587        @Override
1588        public boolean dispatchTouchEvent(MotionEvent ev) {
1589            if (mTouchInterceptor != null && mTouchInterceptor.onTouch(this, ev)) {
1590                return true;
1591            }
1592            return super.dispatchTouchEvent(ev);
1593        }
1594
1595        @Override
1596        public boolean onTouchEvent(MotionEvent event) {
1597            final int x = (int) event.getX();
1598            final int y = (int) event.getY();
1599
1600            if ((event.getAction() == MotionEvent.ACTION_DOWN)
1601                    && ((x < 0) || (x >= getWidth()) || (y < 0) || (y >= getHeight()))) {
1602                dismiss();
1603                return true;
1604            } else if (event.getAction() == MotionEvent.ACTION_OUTSIDE) {
1605                dismiss();
1606                return true;
1607            } else {
1608                return super.onTouchEvent(event);
1609            }
1610        }
1611
1612        @Override
1613        public void sendAccessibilityEvent(int eventType) {
1614            // clinets are interested in the content not the container, make it event source
1615            if (mContentView != null) {
1616                mContentView.sendAccessibilityEvent(eventType);
1617            } else {
1618                super.sendAccessibilityEvent(eventType);
1619            }
1620        }
1621    }
1622
```
可以看到，这里就直接处理的键盘事件和触摸事件，那么就意味着如果我们没有设置`Background`那么在低版本的情况下将会出现无法点击外部消失这个功能，虽然后面的修复了这个问题，但是**Google**也留了一个很大的坑啊，而且为了包装`Background`在展示上的一致性，在高版本无奈只能选择使用两次包裹来实现，也是费尽心思了。。。
### 总结
本篇博客主要分析了`PopupWindow`的实现原理，总的来看，PopupWindow主要是以下几个步骤：
>1. 设置ContentView
>2. 利用自定义View包裹我们的ContentView，自定义View重写了键盘事件和触摸事件分发，实现了点击外部消失
>3. 最终利用WindowManger的addView加入布局，并没有创建新的Window
