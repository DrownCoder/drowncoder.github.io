---
title: "【Window系列】——Dialog源码解析"
date: 2016-02-20 08:00:00 +0800
categories: ["Android源码分析"]
source_name: "【Window系列】——Dialog源码解析"
---
>本系列博客基于android-28版本
[【Window系列】——Toast源码解析](https://www.jianshu.com/p/f9e60e9272cf)
[【Window系列】——PopupWindow的前世今生](https://www.jianshu.com/p/9dafea9cb3c0)
[【Window系列】——Dialog源码解析](https://www.jianshu.com/p/7874bfb20ca0)
[【Window系列】——Window中的Token](https://www.jianshu.com/p/3411ee4cb739)
### 前言
前面两篇博客分别分析了Toast和PopupWindow，本篇博客来分析Dialog和DialogFragment，在早期Android，Dialog一直是弹窗的主力军，自从出了DialogFragment后，其兼容Dialog的特性和Fragment感知生命周期的优势，逐渐替代了Dialog。
### Dialog源码解析
关于`Dialog`的使用方式，首先我们想到的是`AlertDialog`,常规我们的使用方式是如下代码：
```
AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle("问题：");
        builder.setMessage("请问你满十八岁了吗?");
        AlertDialog dialog = builder.create();
        //显示对话框
        dialog.show();
```
看到`Builder`我们第一时间应该就能想到`Builder模式`，Dialog的`Builder`应该是我们最早接触`Builder模式`的实际应用之一，了，从这可以看出`Dialog`涉及的参数很多，所以`Google`选用里`Builder模式`来构建Dialog。
简单的先来看一下`Builder`的源码
```
public Builder(Context context, int themeResId) {
            P = new AlertController.AlertParams(new ContextThemeWrapper(
                    context, resolveDialogTheme(context, themeResId)));
        }
public Builder setTitle(CharSequence title) {
            P.mTitle = title;
            return this;
        }
public Builder setCustomTitle(View customTitleView) {
            P.mCustomTitleView = customTitleView;
            return this;
        }
```
可以看到`Builder`的构造函数里创建了一个`AlertController.AlertParams`对象，而`Builder`设置的参数都是给`AlertController.AlertParams`设置，也就是说`AlertController.AlertParams`是一个`Dialog`参数的包装集成类。
那么来看一下`create`方法。
```
public AlertDialog create() {
            // Context has already been wrapped with the appropriate theme.
            final AlertDialog dialog = new AlertDialog(P.mContext, 0, false);
            //参数赋值
            P.apply(dialog.mAlert);
            dialog.setCancelable(P.mCancelable);
            if (P.mCancelable) {
                dialog.setCanceledOnTouchOutside(true);
            }
            dialog.setOnCancelListener(P.mOnCancelListener);
            dialog.setOnDismissListener(P.mOnDismissListener);
            if (P.mOnKeyListener != null) {
                dialog.setOnKeyListener(P.mOnKeyListener);
            }
            return dialog;
        }
```
可以看到代码很简单，构造了一个`AlertDialog`后，执行了`apply`方法，将刚才设置给`AlertController.AlertParams`赋值给`AlertDialog`,不知道怎么了，看到这个方法名，感觉有点看到`Glide`源码中关于`GlideOptions`的身影，`Glide`源码中对于`GlideOptions`最终也是使用一个`apply`的方式，进行赋值，不知道`Glide`是否是对于这个有一定的参考。
```
public void apply(AlertController dialog) {
            if (mCustomTitleView != null) {
                dialog.setCustomTitle(mCustomTitleView);
            } else {
                if (mTitle != null) {
                    dialog.setTitle(mTitle);
                }
                if (mIcon != null) {
                    dialog.setIcon(mIcon);
                }
                if (mIconId != 0) {
                    dialog.setIcon(mIconId);
                }
                if (mIconAttrId != 0) {
                    dialog.setIcon(dialog.getIconAttributeResId(mIconAttrId));
                }
            }
            if (mMessage != null) {
                dialog.setMessage(mMessage);
            }
            if (mPositiveButtonText != null) {
                dialog.setButton(DialogInterface.BUTTON_POSITIVE, mPositiveButtonText,
                        mPositiveButtonListener, null);
            }
            if (mNegativeButtonText != null) {
                dialog.setButton(DialogInterface.BUTTON_NEGATIVE, mNegativeButtonText,
                        mNegativeButtonListener, null);
            }
            if (mNeutralButtonText != null) {
                dialog.setButton(DialogInterface.BUTTON_NEUTRAL, mNeutralButtonText,
                        mNeutralButtonListener, null);
            }
            if (mForceInverseBackground) {
                dialog.setInverseBackgroundForced(true);
            }
            // For a list, the client can either supply an array of items or an
            // adapter or a cursor
            if ((mItems != null) || (mCursor != null) || (mAdapter != null)) {
            //创建ListView
                createListView(dialog);
            }
            if (mView != null) {
                if (mViewSpacingSpecified) {
                    dialog.setView(mView, mViewSpacingLeft, mViewSpacingTop, mViewSpacingRight,
                            mViewSpacingBottom);
                } else {
                    dialog.setView(mView);
                }
            } else if (mViewLayoutResId != 0) {
                dialog.setView(mViewLayoutResId);
            }

            /*
            dialog.setCancelable(mCancelable);
            dialog.setOnCancelListener(mOnCancelListener);
            if (mOnKeyListener != null) {
                dialog.setOnKeyListener(mOnKeyListener);
            }
            */
        }
```
可以看到，这里基本上将刚才设置给`AlertController.AlertParams`都赋值给了`AlertDialog`，至此，`Builder`和`AlertController.AlertParams`的都完成了自己的作用，最终构建出了`AlertDialog`对象，那么接下来就是`show`方法了。
```
public void show() {
        if (mShowing) {
            if (mDecor != null) {
                if (mWindow.hasFeature(Window.FEATURE_ACTION_BAR)) {
                    mWindow.invalidatePanelMenu(Window.FEATURE_ACTION_BAR);
                }
                mDecor.setVisibility(View.VISIBLE);
            }
            return;
        }

        mCanceled = false;

        if (!mCreated) {
        		//执行onCreate回调
            dispatchOnCreate(null);
        } else {
            // Fill the DecorView in on any configuration changes that
            // may have occured while it was removed from the WindowManager.
            final Configuration config = mContext.getResources().getConfiguration();
            mWindow.getDecorView().dispatchConfigurationChanged(config);
        }
        //执行onStart回调
        onStart();
        mDecor = mWindow.getDecorView();

        if (mActionBar == null && mWindow.hasFeature(Window.FEATURE_ACTION_BAR)) {
            final ApplicationInfo info = mContext.getApplicationInfo();
            mWindow.setDefaultIcon(info.icon);
            mWindow.setDefaultLogo(info.logo);
            mActionBar = new WindowDecorActionBar(this);
        }

        WindowManager.LayoutParams l = mWindow.getAttributes();
        boolean restoreSoftInputMode = false;
        if ((l.softInputMode
                & WindowManager.LayoutParams.SOFT_INPUT_IS_FORWARD_NAVIGATION) == 0) {
            l.softInputMode |=
                    WindowManager.LayoutParams.SOFT_INPUT_IS_FORWARD_NAVIGATION;
            restoreSoftInputMode = true;
        }
        //加入View
        mWindowManager.addView(mDecor, l);
        if (restoreSoftInputMode) {
            l.softInputMode &=
                    ~WindowManager.LayoutParams.SOFT_INPUT_IS_FORWARD_NAVIGATION;
        }

        mShowing = true;
        //利用Handler发送回调
        sendShowMessage();
    }
```
首先来看一下`onCreate`中执行了什么。
```
//Dialog.java
void dispatchOnCreate(Bundle savedInstanceState) {
        if (!mCreated) {
            onCreate(savedInstanceState);
            mCreated = true;
        }
    }
//AlertDialog.java
@Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mAlert.installContent();
    }
//AlertController.java
public void installContent() {
        int contentView = selectContentView();
        //设置根布局文件
        mWindow.setContentView(contentView);
        //设置View相关属性
        setupView();
    }
```
可以看到最终调用了`Window`的`setContentView`方法，看过前面一篇博客（[【重拾View(一)】——setContentView()源码解析](https://www.jianshu.com/p/9e1cf127f0ae)）的应该熟悉这个方法，这个方法是创建`DecorView`并，把我们的布局文件，添加到`DecorView`中。这里注意两点
>1. `Window`的创建的时机，
>2. 根布局文件
这里看到其实`Window`是已经完成了，整个文件中找`Window`的构建过程，可以找到在`Dialog`的构造函数中。
```
Dialog(@NonNull Context context, @StyleRes int themeResId, boolean createContextThemeWrapper) {
        if (createContextThemeWrapper) {
            if (themeResId == ResourceId.ID_NULL) {
                final TypedValue outValue = new TypedValue();
                context.getTheme().resolveAttribute(R.attr.dialogTheme, outValue, true);
                themeResId = outValue.resourceId;
            }
            mContext = new ContextThemeWrapper(context, themeResId);
        } else {
            mContext = context;
        }
        //获取WindowManager
        mWindowManager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
        //构建PhoneWindow
        final Window w = new PhoneWindow(mContext);
        mWindow = w;
        w.setCallback(this);
        w.setOnWindowDismissedCallback(this);
        w.setOnWindowSwipeDismissedCallback(() -> {
            if (mCancelable) {
                cancel();
            }
        });
        w.setWindowManager(mWindowManager, null, null);
        w.setGravity(Gravity.CENTER);
        //创建Handler对象
        mListenersHandler = new ListenersHandler(this);
    }
```
可以看到这里和`Activity`的构建过程相同，也是利用`WindowManager`创建了一个`PhoneWindow`。具体逻辑可以看（[【重拾View(一)】——setContentView()源码解析](https://www.jianshu.com/p/9e1cf127f0ae)）
再看一下根布局文件。
```
private int selectContentView() {
        if (mButtonPanelSideLayout == 0) {
            return mAlertDialogLayout;
        }
        if (mButtonPanelLayoutHint == AlertDialog.LAYOUT_HINT_SIDE) {
            return mButtonPanelSideLayout;
        }
        // TODO: use layout hint side for long messages/lists
        return mAlertDialogLayout;
    }

protected AlertController(Context context, DialogInterface di, Window window) {
        mContext = context;
        mDialogInterface = di;
        mWindow = window;
        mHandler = new ButtonHandler(di);

        final TypedArray a = context.obtainStyledAttributes(null,
                R.styleable.AlertDialog, R.attr.alertDialogStyle, 0);
        //默认的布局文件
        mAlertDialogLayout = a.getResourceId(
                R.styleable.AlertDialog_layout, R.layout.alert_dialog);
        mButtonPanelSideLayout = a.getResourceId(
                R.styleable.AlertDialog_buttonPanelSideLayout, 0);
        mListLayout = a.getResourceId(
                R.styleable.AlertDialog_listLayout, R.layout.select_dialog);

        mMultiChoiceItemLayout = a.getResourceId(
                R.styleable.AlertDialog_multiChoiceItemLayout,
                R.layout.select_dialog_multichoice);
        mSingleChoiceItemLayout = a.getResourceId(
                R.styleable.AlertDialog_singleChoiceItemLayout,
                R.layout.select_dialog_singlechoice);
        mListItemLayout = a.getResourceId(
                R.styleable.AlertDialog_listItemLayout,
                R.layout.select_dialog_item);
        mShowTitle = a.getBoolean(R.styleable.AlertDialog_showTitle, true);

        a.recycle();

        /* We use a custom title so never request a window title */
        window.requestFeature(Window.FEATURE_NO_TITLE);
    }
```
这里可以看到`mAlertDialogLayout`对象是在`AlertController`构造函数时通过读取属性参数，而默认的布局文件是`R.layout.alert_dialog`。
这里简单的看一下这个布局的布局结构，可以看到和我们设置的属性基本是相同。
![dialog_layout.png](https://upload-images.jianshu.io/upload_images/7866586-01034f87cded3307.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
最后看一下`setupView()`
```
private void setupView() {
        final View parentPanel = mWindow.findViewById(R.id.parentPanel);
        final View defaultTopPanel = parentPanel.findViewById(R.id.topPanel);
        final View defaultContentPanel = parentPanel.findViewById(R.id.contentPanel);
        final View defaultButtonPanel = parentPanel.findViewById(R.id.buttonPanel);

        // Install custom content before setting up the title or buttons so
        // that we can handle panel overrides.
        final ViewGroup customPanel = (ViewGroup) parentPanel.findViewById(R.id.customPanel);
        setupCustomContent(customPanel);

        final View customTopPanel = customPanel.findViewById(R.id.topPanel);
        final View customContentPanel = customPanel.findViewById(R.id.contentPanel);
        final View customButtonPanel = customPanel.findViewById(R.id.buttonPanel);

        // Resolve the correct panels and remove the defaults, if needed.
        final ViewGroup topPanel = resolvePanel(customTopPanel, defaultTopPanel);
        final ViewGroup contentPanel = resolvePanel(customContentPanel, defaultContentPanel);
        final ViewGroup buttonPanel = resolvePanel(customButtonPanel, defaultButtonPanel);

        setupContent(contentPanel);
        setupButtons(buttonPanel);
        setupTitle(topPanel);

        final boolean hasCustomPanel = customPanel != null
                && customPanel.getVisibility() != View.GONE;
        final boolean hasTopPanel = topPanel != null
                && topPanel.getVisibility() != View.GONE;
        final boolean hasButtonPanel = buttonPanel != null
                && buttonPanel.getVisibility() != View.GONE;

        // Only display the text spacer if we don't have buttons.
        if (!hasButtonPanel) {
            if (contentPanel != null) {
                final View spacer = contentPanel.findViewById(R.id.textSpacerNoButtons);
                if (spacer != null) {
                    spacer.setVisibility(View.VISIBLE);
                }
            }
            mWindow.setCloseOnTouchOutsideIfNotSet(true);
        }

        if (hasTopPanel) {
            // Only clip scrolling content to padding if we have a title.
            if (mScrollView != null) {
                mScrollView.setClipToPadding(true);
            }

            // Only show the divider if we have a title.
            View divider = null;
            if (mMessage != null || mListView != null || hasCustomPanel) {
                if (!hasCustomPanel) {
                    divider = topPanel.findViewById(R.id.titleDividerNoCustom);
                }
                if (divider == null) {
                    divider = topPanel.findViewById(R.id.titleDivider);
                }

            } else {
                divider = topPanel.findViewById(R.id.titleDividerTop);
            }

            if (divider != null) {
                divider.setVisibility(View.VISIBLE);
            }
        } else {
            if (contentPanel != null) {
                final View spacer = contentPanel.findViewById(R.id.textSpacerNoTitle);
                if (spacer != null) {
                    spacer.setVisibility(View.VISIBLE);
                }
            }
        }

        if (mListView instanceof RecycleListView) {
            ((RecycleListView) mListView).setHasDecor(hasTopPanel, hasButtonPanel);
        }

        // Update scroll indicators as needed.
        if (!hasCustomPanel) {
            final View content = mListView != null ? mListView : mScrollView;
            if (content != null) {
                final int indicators = (hasTopPanel ? View.SCROLL_INDICATOR_TOP : 0)
                        | (hasButtonPanel ? View.SCROLL_INDICATOR_BOTTOM : 0);
                content.setScrollIndicators(indicators,
                        View.SCROLL_INDICATOR_TOP | View.SCROLL_INDICATOR_BOTTOM);
            }
        }

        final TypedArray a = mContext.obtainStyledAttributes(
                null, R.styleable.AlertDialog, R.attr.alertDialogStyle, 0);
        setBackground(a, topPanel, contentPanel, customPanel, buttonPanel,
                hasTopPanel, hasCustomPanel, hasButtonPanel);
        a.recycle();
    }
```
不出意外，就是将我们设置的属性，分别设置到布局文件上对应的View上，至此，我们通过`Builder`设置的参数属性，就设置到`DecorView`上。剩下的就是将`DecorView`加入到`PhoneWindow`上，然后调用`mWindowManager.addView(mDecor, l);`这个方法后会执行到ViewRootImpl，等到下个屏幕信号到来时就会刷新出来。
### DialogFragment源码解析
本篇博客主要讲解的是`Dialog`相关的源码解析，所以侧重点主要是和`Dialog`相关的，涉及到`Fragment`相关的知识点，这里就不做详细的讲解了。
查看`DialogFragment`相关的源码会发现`Dialog`的身影。
```
@Override
    @NonNull
    public LayoutInflater onGetLayoutInflater(@Nullable Bundle savedInstanceState) {
        if (!mShowsDialog) {
            return super.onGetLayoutInflater(savedInstanceState);
        }
        //创建Dialog
        mDialog = onCreateDialog(savedInstanceState);

        if (mDialog != null) {
        	  //设置Dialog属性
            setupDialog(mDialog, mStyle);

            return (LayoutInflater) mDialog.getContext().getSystemService(
                    Context.LAYOUT_INFLATER_SERVICE);
        }
        return (LayoutInflater) mHost.getContext().getSystemService(
                Context.LAYOUT_INFLATER_SERVICE);
    }
```
可以看到这里创建了一个`Dialog`，但我们可能对于这个方法比较陌生`onGetLayoutInflater `，找寻这个方法对调用链，最终我们会在`FragmentManagerImpl`中找到。
```
f.performCreateView(f.performGetLayoutInflater(
                                    f.mSavedFragmentState), container, f.mSavedFragmentState);
                                    
@NonNull
    LayoutInflater performGetLayoutInflater(@Nullable Bundle savedInstanceState) {
        LayoutInflater layoutInflater = onGetLayoutInflater(savedInstanceState);
        mLayoutInflater = layoutInflater;
        return mLayoutInflater;
    }
```
所以我们就知道了，在`DialogFragment`回调`onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,@Nullable Bundle savedInstanceState)`方法的时候，就会创建一个`Dialog`对象。
我们接下来沿着`Fragment`生命周期继续向下看，在`onActivityCreate`中又一次看到了`Dialog`的身影。
```
@Override
    public void onActivityCreated(@Nullable Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);

        if (!mShowsDialog) {
            return;
        }

        View view = getView();
        if (view != null) {
            if (view.getParent() != null) {
                throw new IllegalStateException(
                        "DialogFragment can not be attached to a container view");
            }
            //设置ContentView到Dialog中
            mDialog.setContentView(view);
        }
        final Activity activity = getActivity();
        if (activity != null) {
            mDialog.setOwnerActivity(activity);
        }
        mDialog.setCancelable(mCancelable);
        mDialog.setOnCancelListener(this);
        mDialog.setOnDismissListener(this);
        if (savedInstanceState != null) {
            Bundle dialogState = savedInstanceState.getBundle(SAVED_DIALOG_STATE_TAG);
            if (dialogState != null) {
                mDialog.onRestoreInstanceState(dialogState);
            }
        }
    }
@Nullable
    public View getView() {
        return mView;
    }
```
这里可以看到，首先保存了我们在`onCreateView`中返回的`View`对象，然后设置到了`Dialog`到`ContentView`中，也就是说我们在`DialogFragment`中设置到布局，最终其实是以`Dialog`到形式展示的。
```
@Override
    public void onStart() {
        super.onStart();

        if (mDialog != null) {
            mViewDestroyed = false;
            mDialog.show();
        }
    }
```
紧接着在`onStart`方法中，直接调用了`show`方法，将Dialog显示出来了。
```
@Override
    public void onStop() {
        super.onStop();
        if (mDialog != null) {
            mDialog.hide();
        }
    }

    /**
     * Remove dialog.
     */
    @Override
    public void onDestroyView() {
        super.onDestroyView();
        if (mDialog != null) {
            // Set removed here because this dismissal is just to hide
            // the dialog -- we don't want this to cause the fragment to
            // actually be removed.
            mViewDestroyed = true;
            // Instead of waiting for a posted onDismiss(), null out
            // the listener and call onDismiss() manually to ensure
            // that the callback happens before onDestroy()
            mDialog.setOnDismissListener(null);
            mDialog.dismiss();
            if (!mDismissed) {
                // Don't send a second onDismiss() callback if we've already
                // dismissed the dialog manually in dismissInternal()
                onDismiss(mDialog);
            }
            mDialog = null;
        }
    }
```
后面对应的生命周期中，分别在`onStop`方法中利用`hide`方法隐藏了`Dialog`,而在`onDestroyView`中，`dismiss`了`Dialog`。
### 总结
所以最终我们会发现，其实`DialogFragment`整个生命周期中贯穿着对于`Dialog`的使用，`DialogFragment`其实是对于`Dialog`的一种**包装类**的思想，不仅将`Dialog`单独抽出来成为一个个体，并且利用`Fragment`的特性，赋予了`Dialog`生命周期的能力，可以看出`Google`对于`Frament`感知生命周期的特性的利用其实很早就已经开始了，而`Google`新出的`JetPack`框架中也是重复利用了`Fragment`的特性完成的。
本篇博客只是讲解了`Dialog`的源码实现和`DialogFragment`的拓展使用，但是`Dialog`还有一个更为重要的知识点这里没有分析，和前面几篇博客一样，就是对于`token`对象的分析。熟悉`Dialog`的应该清楚，`Dialog`的构建必须传入一个`Activity`类型的`Context`，如果传入的是`Application`，则会抛异常，这里面的缘由也是由于`token`对象引起的，所以下一篇博客应该是**【Window】**系列的终篇，讲一讲关于`Window`中`token`和`type`的那些事。
