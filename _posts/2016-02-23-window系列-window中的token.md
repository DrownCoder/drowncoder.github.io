---
title: "【Window系列】——Window中的Token"
date: 2020-04-19 18:20:38+08:00
categories: ["Android源码分析"]
source_name: "【Window系列】——Window中的Token"
jianshu_views: 2372
jianshu_url: "https://www.jianshu.com/p/3411ee4cb739"
---
>本系列博客基于android-28版本
[【Window系列】——Toast源码解析](https://www.jianshu.com/p/f9e60e9272cf)
[【Window系列】——PopupWindow的前世今生](https://www.jianshu.com/p/9dafea9cb3c0)
[【Window系列】——Dialog源码解析](https://www.jianshu.com/p/7874bfb20ca0)
[【Window系列】——Window中的Token](https://www.jianshu.com/p/3411ee4cb739)
### 前言
距离上一次发博客已经过了10个月了~中途因为换了工作，所以一直在忙工作的事，后面会慢慢恢复博客的进度，博客还是会坚持的！！！  
本次博客还是接着上次博客的介绍，这篇博客应该是对Window系列的收尾，前三篇博客都提到了关于Token变量，这篇博客就来分析一下Token在Window的使用中的重要性。
### 源码分析
#### addView的主体流程
看过前面三篇博客的应该都会发现，无论是`PopupWindow`还是`Dialog`还是`Toast`，三者的最终原理都是使用`WindowManager.addView`来加入View的。而我们这回要学习的`Token`其实就是和这个方法的流程有关，所以要搞清楚`Token`的作用，肯定首先要了解`WindowManager.addView`的原理。
既然是看方法的作用，那么我们首先来看一下`WindowManager`的构建过程。看过前三篇博客应该都了解`WindowManager`的创建一般都是这样。  
```
mWindowManager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
```
既然是`Context`，那么这里就来看一下`Activity`的`getSystemService`方法（这里为什么要看`Activity`后面会有讲解）
```
@Override
    public Object getSystemService(@ServiceName @NonNull String name) {
        if (getBaseContext() == null) {
            throw new IllegalStateException(
                    "System services not available to Activities before onCreate()");
        }
		//如果是WindowService，直接返回Activity的实例
        if (WINDOW_SERVICE.equals(name)) {
            return mWindowManager;
        } else if (SEARCH_SERVICE.equals(name)) {
            ensureSearchManager();
            return mSearchManager;
        }
        return super.getSystemService(name);
    }
```
可以看到`Google`也会有`ifelse`~~~，这里其实是做了特殊判断，如果是`WINDOW_SERVICE`，那么就会返回`Activity`中的`mWindowManager`。那么我们可以看一下`Activity`中这个对象是怎么创建的。
```
final void attach(Context context, ActivityThread aThread,
            Instrumentation instr, IBinder token, int ident,
            Application application, Intent intent, ActivityInfo info,
            CharSequence title, Activity parent, String id,
            NonConfigurationInstances lastNonConfigurationInstances,
            Configuration config, String referrer, IVoiceInteractor voiceInteractor,
            Window window, ActivityConfigCallback activityConfigCallback) {
        attachBaseContext(context);

        mFragments.attachHost(null /*parent*/);

        mWindow = new PhoneWindow(this, window, activityConfigCallback);
        ...

        mWindow.setWindowManager(
                (WindowManager)context.getSystemService(Context.WINDOW_SERVICE),
                mToken, mComponent.flattenToString(),
                (info.flags & ActivityInfo.FLAG_HARDWARE_ACCELERATED) != 0);
        if (mParent != null) {
            mWindow.setContainer(mParent.getWindow());
        }
		//创建WindowManager
        mWindowManager = mWindow.getWindowManager();
        mCurrentConfig = config;

        mWindow.setColorMode(info.colorMode);
    }
```
可以看到在`Activity`的`attach`方法中可以看到`WindowManager`的构建，那我们继续来看一下`Window`中的方法，这里其实也可以看到`Window`的实现类其实是`PhoneWindow`。
```
public void setWindowManager(WindowManager wm, IBinder appToken, String appName,
            boolean hardwareAccelerated) {
        mAppToken = appToken;
        mAppName = appName;
        mHardwareAccelerated = hardwareAccelerated
                || SystemProperties.getBoolean(PROPERTY_HARDWARE_UI, false);
        if (wm == null) {
            wm = (WindowManager)mContext.getSystemService(Context.WINDOW_SERVICE);
        }
		//创建WindowManager
        mWindowManager = ((WindowManagerImpl)wm).createLocalWindowManager(this);
    }
```
这里其实通过强转已经可以看到我们需要了解`WindowManager`的实现类就是`WindowManagerImpl`，于是我们可以看看`addView`是怎么实现的
```
@Override
    public void addView(@NonNull View view, @NonNull ViewGroup.LayoutParams params) {
        applyDefaultToken(params);
        mGlobal.addView(view, params, mContext.getDisplay(), mParentWindow);
    }
```
好吧，又通过其他类代理了，那么继续看一下`mGlobal`对象是什么。
```
public final class WindowManagerImpl implements WindowManager {
    private final WindowManagerGlobal mGlobal = WindowManagerGlobal.getInstance();
...
}
```
这里就简单多了，可以看到`mGlobal`是一个`WindowManagerGlobal`对象，并且这个对象是一个`final`对象。在`WindowManagerGlobal`对象中我们终于看到了`addView`的实现
```
public void addView(View view, ViewGroup.LayoutParams params,
            Display display, Window parentWindow) {
        ....

        final WindowManager.LayoutParams wparams = (WindowManager.LayoutParams) params;
        if (parentWindow != null) {
		//设置token
            parentWindow.adjustLayoutParamsForSubWindow(wparams);
        } else {
            // If there's no parent, then hardware acceleration for this view is
            // set from the application's hardware acceleration setting.
            final Context context = view.getContext();
            if (context != null
                    && (context.getApplicationInfo().flags
                            & ApplicationInfo.FLAG_HARDWARE_ACCELERATED) != 0) {
                wparams.flags |= WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED;
            }
        }

        ViewRootImpl root;
        View panelParentView = null;
       ...
		//创建ViewRootImpl
        root = new ViewRootImpl(view.getContext(), display);

            view.setLayoutParams(wparams);

            mViews.add(view);
            mRoots.add(root);
            mParams.add(wparams);

            // do this last because it fires off messages to start doing things
            try {
			//setView方法
                root.setView(view, wparams, panelParentView);
            } catch (RuntimeException e) {
                // BadTokenException or InvalidDisplayException, clean up.
                if (index >= 0) {
                    removeViewLocked(index, true);
                }
                throw e;
            }
        }
    }
```
这里其实有三个重要的步骤
* 1. 设置Token
* 2. 初始化ViewRootImpl
* 3. 调用setView方法

其中第一个步骤`parentWindow.adjustLayoutParamsForSubWindow(wparams);`通过方法名我们可以简单的看出来这个方法的作用是通过parent给子Window设置param，这里先不详细展开方法的内部（后面会分析到）。  
而第二个和第三个步骤，熟悉**Activity的View的绘制流程的**其实应该对于这两个方法很熟悉，这个其实就是我们View绘制起始的地方。由于本篇博客不是详细讲解**View的绘制流程**的，所以这里不对于这个方法详细展开，后面如果有必要会专门写博客分析这个地方（因为网上这类的博客实在太多了），这里先说一下结论吧，我们调用`setView`是怎么能显示到页面中的呢，在`setView`中会调用会有这样一个代码。
```
try {
                    mOrigWindowType = mWindowAttributes.type;
                    mAttachInfo.mRecomputeGlobalAttributes = true;
                    collectViewAttributes();
					//通过IPC加入View
                    res = mWindowSession.addToDisplay(mWindow, mSeq, mWindowAttributes,
                            getHostVisibility(), mDisplay.getDisplayId(),
                            mAttachInfo.mContentInsets, mAttachInfo.mStableInsets,
                            mAttachInfo.mOutsets, mInputChannel);
                } catch (RemoteException e)
```
这里会通过IPC调用`mWindowSession.addToDisplay`，简单说一下调用链，`mWindowSession`的`addToDisplay`使用的是`Session`的`addToDisplay`方法
```
public class Session extends IWindowSession.Stub
        implements IBinder.DeathRecipient {
    final WindowManagerService mService;
	@Override
    public int addToDisplay(IWindow window, int seq, WindowManager.LayoutParams attrs,
            int viewVisibility, int displayId, Rect outContentInsets, Rect outStableInsets,
            Rect outOutsets, InputChannel outInputChannel) {
        return mService.addWindow(this, window, seq, attrs, viewVisibility, displayId,
                outContentInsets, outStableInsets, outOutsets, outInputChannel);
    }
}
```
终于看到这里的主人公了，这里可以看到调用的`WindowManagerService`的`addWindow`方法。
```
public int addWindow(Session session, IWindow client, int seq,
            WindowManager.LayoutParams attrs, int viewVisibility, int displayId,
            Rect outContentInsets, Rect outStableInsets, Rect outOutsets,
            InputChannel outInputChannel) {
        int[] appOp = new int[1];
		//校验权限
        int res = mPolicy.checkAddPermission(attrs, appOp);
        if (res != WindowManagerGlobal.ADD_OKAY) {
            return res;
        }

        boolean reportNewConfig = false;
        WindowState parentWindow = null;
        long origId;
        final int callingUid = Binder.getCallingUid();
        final int type = attrs.type;

        synchronized(mWindowMap) {
            if (!mDisplayReady) {
                throw new IllegalStateException("Display has not been initialialized");
            }

            final DisplayContent displayContent = mRoot.getDisplayContentOrCreate(displayId);
            if (displayContent == null) {
                Slog.w(TAG_WM, "Attempted to add window to a display that does not exist: "
                        + displayId + ".  Aborting.");
                return WindowManagerGlobal.ADD_INVALID_DISPLAY;
            }
            if (!displayContent.hasAccess(session.mUid)
                    && !mDisplayManagerInternal.isUidPresentOnDisplay(session.mUid, displayId)) {
                Slog.w(TAG_WM, "Attempted to add window to a display for which the application "
                        + "does not have access: " + displayId + ".  Aborting.");
                return WindowManagerGlobal.ADD_INVALID_DISPLAY;
            }

            if (mWindowMap.containsKey(client.asBinder())) {
                Slog.w(TAG_WM, "Window " + client + " is already added");
                return WindowManagerGlobal.ADD_DUPLICATE_ADD;
            }
			//type判断
            if (type >= FIRST_SUB_WINDOW && type <= LAST_SUB_WINDOW) {
                parentWindow = windowForClientLocked(null, attrs.token, false);
                if (parentWindow == null) {
                    Slog.w(TAG_WM, "Attempted to add window with token that is not a window: "
                          + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_SUBWINDOW_TOKEN;
                }
                if (parentWindow.mAttrs.type >= FIRST_SUB_WINDOW
                        && parentWindow.mAttrs.type <= LAST_SUB_WINDOW) {
                    Slog.w(TAG_WM, "Attempted to add window with token that is a sub-window: "
                            + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_SUBWINDOW_TOKEN;
                }
            }

            if (type == TYPE_PRIVATE_PRESENTATION && !displayContent.isPrivate()) {
                Slog.w(TAG_WM, "Attempted to add private presentation window to a non-private display.  Aborting.");
                return WindowManagerGlobal.ADD_PERMISSION_DENIED;
            }

            AppWindowToken atoken = null;
            final boolean hasParent = parentWindow != null;
            // Use existing parent window token for child windows since they go in the same token
            // as there parent window so we can apply the same policy on them.
            WindowToken token = displayContent.getWindowToken(
                    hasParent ? parentWindow.mAttrs.token : attrs.token);
            // If this is a child window, we want to apply the same type checking rules as the
            // parent window type.
            final int rootType = hasParent ? parentWindow.mAttrs.type : type;

            boolean addToastWindowRequiresToken = false;

            if (token == null) {
                if (rootType >= FIRST_APPLICATION_WINDOW && rootType <= LAST_APPLICATION_WINDOW) {
                    Slog.w(TAG_WM, "Attempted to add application window with unknown token "
                          + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
                if (rootType == TYPE_INPUT_METHOD) {
                    Slog.w(TAG_WM, "Attempted to add input method window with unknown token "
                          + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
                if (rootType == TYPE_VOICE_INTERACTION) {
                    Slog.w(TAG_WM, "Attempted to add voice interaction window with unknown token "
                          + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
                if (rootType == TYPE_WALLPAPER) {
                    Slog.w(TAG_WM, "Attempted to add wallpaper window with unknown token "
                          + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
                if (rootType == TYPE_DREAM) {
                    Slog.w(TAG_WM, "Attempted to add Dream window with unknown token "
                          + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
                if (rootType == TYPE_QS_DIALOG) {
                    Slog.w(TAG_WM, "Attempted to add QS dialog window with unknown token "
                          + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
                if (rootType == TYPE_ACCESSIBILITY_OVERLAY) {
                    Slog.w(TAG_WM, "Attempted to add Accessibility overlay window with unknown token "
                            + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
                if (type == TYPE_TOAST) {
                    // Apps targeting SDK above N MR1 cannot arbitrary add toast windows.
                    if (doesAddToastWindowRequireToken(attrs.packageName, callingUid,
                            parentWindow)) {
                        Slog.w(TAG_WM, "Attempted to add a toast window with unknown token "
                                + attrs.token + ".  Aborting.");
                        return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                    }
                }
                final IBinder binder = attrs.token != null ? attrs.token : client.asBinder();
                token = new WindowToken(this, binder, type, false, displayContent,
                        session.mCanAddInternalSystemWindow);
            } else if (rootType >= FIRST_APPLICATION_WINDOW && rootType <= LAST_APPLICATION_WINDOW) {
                atoken = token.asAppWindowToken();
                if (atoken == null) {
                    Slog.w(TAG_WM, "Attempted to add window with non-application token "
                          + token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_NOT_APP_TOKEN;
                } else if (atoken.removed) {
                    Slog.w(TAG_WM, "Attempted to add window with exiting application token "
                          + token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_APP_EXITING;
                }
            } else if (rootType == TYPE_INPUT_METHOD) {
                if (token.windowType != TYPE_INPUT_METHOD) {
                    Slog.w(TAG_WM, "Attempted to add input method window with bad token "
                            + attrs.token + ".  Aborting.");
                      return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
            } else if (rootType == TYPE_VOICE_INTERACTION) {
                if (token.windowType != TYPE_VOICE_INTERACTION) {
                    Slog.w(TAG_WM, "Attempted to add voice interaction window with bad token "
                            + attrs.token + ".  Aborting.");
                      return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
            } else if (rootType == TYPE_WALLPAPER) {
                if (token.windowType != TYPE_WALLPAPER) {
                    Slog.w(TAG_WM, "Attempted to add wallpaper window with bad token "
                            + attrs.token + ".  Aborting.");
                      return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
            } else if (rootType == TYPE_DREAM) {
                if (token.windowType != TYPE_DREAM) {
                    Slog.w(TAG_WM, "Attempted to add Dream window with bad token "
                            + attrs.token + ".  Aborting.");
                      return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
            } else if (rootType == TYPE_ACCESSIBILITY_OVERLAY) {
                if (token.windowType != TYPE_ACCESSIBILITY_OVERLAY) {
                    Slog.w(TAG_WM, "Attempted to add Accessibility overlay window with bad token "
                            + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
            } else if (type == TYPE_TOAST) {
                // Apps targeting SDK above N MR1 cannot arbitrary add toast windows.
                addToastWindowRequiresToken = doesAddToastWindowRequireToken(attrs.packageName,
                        callingUid, parentWindow);
                if (addToastWindowRequiresToken && token.windowType != TYPE_TOAST) {
                    Slog.w(TAG_WM, "Attempted to add a toast window with bad token "
                            + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
            } else if (type == TYPE_QS_DIALOG) {
                if (token.windowType != TYPE_QS_DIALOG) {
                    Slog.w(TAG_WM, "Attempted to add QS dialog window with bad token "
                            + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
            } else if (token.asAppWindowToken() != null) {
                Slog.w(TAG_WM, "Non-null appWindowToken for system window of rootType=" + rootType);
                // It is not valid to use an app token with other system types; we will
                // instead make a new token for it (as if null had been passed in for the token).
                attrs.token = null;
                token = new WindowToken(this, client.asBinder(), type, false, displayContent,
                        session.mCanAddInternalSystemWindow);
            }

            final WindowState win = new WindowState(this, session, client, token, parentWindow,
                    appOp[0], seq, attrs, viewVisibility, session.mUid,
                    session.mCanAddInternalSystemWindow);
            if (win.mDeathRecipient == null) {
                // Client has apparently died, so there is no reason to
                // continue.
                Slog.w(TAG_WM, "Adding window client " + client.asBinder()
                        + " that is dead, aborting.");
                return WindowManagerGlobal.ADD_APP_EXITING;
            }

            if (win.getDisplayContent() == null) {
                Slog.w(TAG_WM, "Adding window to Display that has been removed.");
                return WindowManagerGlobal.ADD_INVALID_DISPLAY;
            }

            mPolicy.adjustWindowParamsLw(win.mAttrs);
            win.setShowToOwnerOnlyLocked(mPolicy.checkShowToOwnerOnly(attrs));

            res = mPolicy.prepareAddWindowLw(win, attrs);
            if (res != WindowManagerGlobal.ADD_OKAY) {
                return res;
            }

            final boolean openInputChannels = (outInputChannel != null
                    && (attrs.inputFeatures & INPUT_FEATURE_NO_INPUT_CHANNEL) == 0);
            if  (openInputChannels) {
                win.openInputChannel(outInputChannel);
            }

            // If adding a toast requires a token for this app we always schedule hiding
            // toast windows to make sure they don't stick around longer then necessary.
            // We hide instead of remove such windows as apps aren't prepared to handle
            // windows being removed under them.
            //
            // If the app is older it can add toasts without a token and hence overlay
            // other apps. To be maximally compatible with these apps we will hide the
            // window after the toast timeout only if the focused window is from another
            // UID, otherwise we allow unlimited duration. When a UID looses focus we
            // schedule hiding all of its toast windows.
            if (type == TYPE_TOAST) {
                if (!getDefaultDisplayContentLocked().canAddToastWindowForUid(callingUid)) {
                    Slog.w(TAG_WM, "Adding more than one toast window for UID at a time.");
                    return WindowManagerGlobal.ADD_DUPLICATE_ADD;
                }
                // Make sure this happens before we moved focus as one can make the
                // toast focusable to force it not being hidden after the timeout.
                // Focusable toasts are always timed out to prevent a focused app to
                // show a focusable toasts while it has focus which will be kept on
                // the screen after the activity goes away.
                if (addToastWindowRequiresToken
                        || (attrs.flags & LayoutParams.FLAG_NOT_FOCUSABLE) == 0
                        || mCurrentFocus == null
                        || mCurrentFocus.mOwnerUid != callingUid) {
                    mH.sendMessageDelayed(
                            mH.obtainMessage(H.WINDOW_HIDE_TIMEOUT, win),
                            win.mAttrs.hideTimeoutMilliseconds);
                }
            }

            // From now on, no exceptions or errors allowed!

            res = WindowManagerGlobal.ADD_OKAY;
            if (mCurrentFocus == null) {
                mWinAddedSinceNullFocus.add(win);
            }

            if (excludeWindowTypeFromTapOutTask(type)) {
                displayContent.mTapExcludedWindows.add(win);
            }

            origId = Binder.clearCallingIdentity();

            win.attach();
            mWindowMap.put(client.asBinder(), win);
            if (win.mAppOp != AppOpsManager.OP_NONE) {
                int startOpResult = mAppOps.startOpNoThrow(win.mAppOp, win.getOwningUid(),
                        win.getOwningPackage());
                if ((startOpResult != AppOpsManager.MODE_ALLOWED) &&
                        (startOpResult != AppOpsManager.MODE_DEFAULT)) {
                    win.setAppOpVisibilityLw(false);
                }
            }

            final AppWindowToken aToken = token.asAppWindowToken();
            if (type == TYPE_APPLICATION_STARTING && aToken != null) {
                aToken.startingWindow = win;
                if (DEBUG_STARTING_WINDOW) Slog.v (TAG_WM, "addWindow: " + aToken
                        + " startingWindow=" + win);
            }

            boolean imMayMove = true;

            win.mToken.addWindow(win);
            if (type == TYPE_INPUT_METHOD) {
                win.mGivenInsetsPending = true;
                setInputMethodWindowLocked(win);
                imMayMove = false;
            } else if (type == TYPE_INPUT_METHOD_DIALOG) {
                displayContent.computeImeTarget(true /* updateImeTarget */);
                imMayMove = false;
            } else {
                if (type == TYPE_WALLPAPER) {
                    displayContent.mWallpaperController.clearLastWallpaperTimeoutTime();
                    displayContent.pendingLayoutChanges |= FINISH_LAYOUT_REDO_WALLPAPER;
                } else if ((attrs.flags&FLAG_SHOW_WALLPAPER) != 0) {
                    displayContent.pendingLayoutChanges |= FINISH_LAYOUT_REDO_WALLPAPER;
                } else if (displayContent.mWallpaperController.isBelowWallpaperTarget(win)) {
                    // If there is currently a wallpaper being shown, and
                    // the base layer of the new window is below the current
                    // layer of the target window, then adjust the wallpaper.
                    // This is to avoid a new window being placed between the
                    // wallpaper and its target.
                    displayContent.pendingLayoutChanges |= FINISH_LAYOUT_REDO_WALLPAPER;
                }
            }

            // If the window is being added to a stack that's currently adjusted for IME,
            // make sure to apply the same adjust to this new window.
            win.applyAdjustForImeIfNeeded();

            if (type == TYPE_DOCK_DIVIDER) {
                mRoot.getDisplayContent(displayId).getDockedDividerController().setWindow(win);
            }

            final WindowStateAnimator winAnimator = win.mWinAnimator;
            winAnimator.mEnterAnimationPending = true;
            winAnimator.mEnteringAnimation = true;
            // Check if we need to prepare a transition for replacing window first.
            if (atoken != null && atoken.isVisible()
                    && !prepareWindowReplacementTransition(atoken)) {
                // If not, check if need to set up a dummy transition during display freeze
                // so that the unfreeze wait for the apps to draw. This might be needed if
                // the app is relaunching.
                prepareNoneTransitionForRelaunching(atoken);
            }

            if (displayContent.isDefaultDisplay) {
                final DisplayInfo displayInfo = displayContent.getDisplayInfo();
                final Rect taskBounds;
                if (atoken != null && atoken.getTask() != null) {
                    taskBounds = mTmpRect;
                    atoken.getTask().getBounds(mTmpRect);
                } else {
                    taskBounds = null;
                }
                if (mPolicy.getInsetHintLw(win.mAttrs, taskBounds, displayInfo.rotation,
                        displayInfo.logicalWidth, displayInfo.logicalHeight, outContentInsets,
                        outStableInsets, outOutsets)) {
                    res |= WindowManagerGlobal.ADD_FLAG_ALWAYS_CONSUME_NAV_BAR;
                }
            } else {
                outContentInsets.setEmpty();
                outStableInsets.setEmpty();
            }

            if (mInTouchMode) {
                res |= WindowManagerGlobal.ADD_FLAG_IN_TOUCH_MODE;
            }
            if (win.mAppToken == null || !win.mAppToken.isClientHidden()) {
                res |= WindowManagerGlobal.ADD_FLAG_APP_VISIBLE;
            }

            mInputMonitor.setUpdateInputWindowsNeededLw();

            boolean focusChanged = false;
            if (win.canReceiveKeys()) {
                focusChanged = updateFocusedWindowLocked(UPDATE_FOCUS_WILL_ASSIGN_LAYERS,
                        false /*updateInputWindows*/);
                if (focusChanged) {
                    imMayMove = false;
                }
            }

            if (imMayMove) {
                displayContent.computeImeTarget(true /* updateImeTarget */);
            }

            // Don't do layout here, the window must call
            // relayout to be displayed, so we'll do it there.
            displayContent.assignWindowLayers(false /* setLayoutNeeded */);

            if (focusChanged) {
                mInputMonitor.setInputFocusLw(mCurrentFocus, false /*updateInputWindows*/);
            }
            mInputMonitor.updateInputWindowsLw(false /*force*/);

            if (localLOGV || DEBUG_ADD_REMOVE) Slog.v(TAG_WM, "addWindow: New client "
                    + client.asBinder() + ": window=" + win + " Callers=" + Debug.getCallers(5));

            if (win.isVisibleOrAdding() && updateOrientationFromAppTokensLocked(false, displayId)) {
                reportNewConfig = true;
            }
        }

        if (reportNewConfig) {
            sendNewConfiguration(displayId);
        }

        Binder.restoreCallingIdentity(origId);

        return res;
    }
```
从上面我们可以关注到两个地方，第一个是这里会先判断权限，第二就是这里会判断token，如果不满足则直接返回，这里的返回则还会通过IPC返回到我们刚才的`ViewRootIml`的`setView`的方法里。
```
public void setView(View view, WindowManager.LayoutParams attrs, View panelParentView) {
        synchronized (this) {
            if (mView == null) {
                mView = view;

               ...
                int res; /* = WindowManagerImpl.ADD_OKAY; */

                // Schedule the first layout -before- adding to the window
                // manager, to make sure we do the relayout before receiving
                // any other events from the system.
                requestLayout();
                if ((mWindowAttributes.inputFeatures
                        & WindowManager.LayoutParams.INPUT_FEATURE_NO_INPUT_CHANNEL) == 0) {
                    mInputChannel = new InputChannel();
                }
                mForceDecorViewVisibility = (mWindowAttributes.privateFlags
                        & PRIVATE_FLAG_FORCE_DECOR_VIEW_VISIBILITY) != 0;
                try {
                    mOrigWindowType = mWindowAttributes.type;
                    mAttachInfo.mRecomputeGlobalAttributes = true;
                    collectViewAttributes();
					//获取addView的返回值
                    res = mWindowSession.addToDisplay(mWindow, mSeq, mWindowAttributes,
                            getHostVisibility(), mDisplay.getDisplayId(),
                            mAttachInfo.mContentInsets, mAttachInfo.mStableInsets,
                            mAttachInfo.mOutsets, mInputChannel);
                } catch (RemoteException e) {
                    mAdded = false;
                    mView = null;
                    mAttachInfo.mRootView = null;
                    mInputChannel = null;
                    mFallbackEventHandler.setView(null);
                    unscheduleTraversals();
                    setAccessibilityFocus(null, null);
                    throw new RuntimeException("Adding window failed", e);
                } finally {
                    if (restore) {
                        attrs.restore();
                    }
                }

                if (mTranslator != null) {
                    mTranslator.translateRectInScreenToAppWindow(mAttachInfo.mContentInsets);
                }
                mPendingOverscanInsets.set(0, 0, 0, 0);
                mPendingContentInsets.set(mAttachInfo.mContentInsets);
                mPendingStableInsets.set(mAttachInfo.mStableInsets);
                mPendingVisibleInsets.set(0, 0, 0, 0);
                mAttachInfo.mAlwaysConsumeNavBar =
                        (res & WindowManagerGlobal.ADD_FLAG_ALWAYS_CONSUME_NAV_BAR) != 0;
                mPendingAlwaysConsumeNavBar = mAttachInfo.mAlwaysConsumeNavBar;
                if (DEBUG_LAYOUT) Log.v(mTag, "Added window " + mWindow);
				//判断返回值是否异常
                if (res < WindowManagerGlobal.ADD_OKAY) {
                    mAttachInfo.mRootView = null;
                    mAdded = false;
                    mFallbackEventHandler.setView(null);
                    unscheduleTraversals();
                    setAccessibilityFocus(null, null);
                    switch (res) {
                        case WindowManagerGlobal.ADD_BAD_APP_TOKEN:
                        case WindowManagerGlobal.ADD_BAD_SUBWINDOW_TOKEN:
                            throw new WindowManager.BadTokenException(
                                    "Unable to add window -- token " + attrs.token
                                    + " is not valid; is your activity running?");
                        case WindowManagerGlobal.ADD_NOT_APP_TOKEN:
                            throw new WindowManager.BadTokenException(
                                    "Unable to add window -- token " + attrs.token
                                    + " is not for an application");
                        case WindowManagerGlobal.ADD_APP_EXITING:
                            throw new WindowManager.BadTokenException(
                                    "Unable to add window -- app for token " + attrs.token
                                    + " is exiting");
                        case WindowManagerGlobal.ADD_DUPLICATE_ADD:
                            throw new WindowManager.BadTokenException(
                                    "Unable to add window -- window " + mWindow
                                    + " has already been added");
                        case WindowManagerGlobal.ADD_STARTING_NOT_NEEDED:
                            // Silently ignore -- we would have just removed it
                            // right away, anyway.
                            return;
                        case WindowManagerGlobal.ADD_MULTIPLE_SINGLETON:
                            throw new WindowManager.BadTokenException("Unable to add window "
                                    + mWindow + " -- another window of type "
                                    + mWindowAttributes.type + " already exists");
                        case WindowManagerGlobal.ADD_PERMISSION_DENIED:
                            throw new WindowManager.BadTokenException("Unable to add window "
                                    + mWindow + " -- permission denied for window type "
                                    + mWindowAttributes.type);
                        case WindowManagerGlobal.ADD_INVALID_DISPLAY:
                            throw new WindowManager.InvalidDisplayException("Unable to add window "
                                    + mWindow + " -- the specified display can not be found");
                        case WindowManagerGlobal.ADD_INVALID_TYPE:
                            throw new WindowManager.InvalidDisplayException("Unable to add window "
                                    + mWindow + " -- the specified window type "
                                    + mWindowAttributes.type + " is not valid");
                    }
                    throw new RuntimeException(
                            "Unable to add window -- unknown error code " + res);
                }

                ...
            }
        }
    }
```
可以看到我们拿到返回值，如果有错误，我们经常碰到的`BadTokenException`异常就在这里碰到了。
到这里我们大体流程上应该有一个：
* 1.无论是`PopupWindow`还是`Dialog`还是`Toast`，三者的最终原理都是使用`WindowManager.addView`来加入View的
* 2.`WindowManager`是在Activity的`attach`方法创建的，`Window`的实现类是`PhoneWindow`,而`WindowManager`的实现类是`WindowManagerGlobal`。
* 3.最终`addView`的方法会调用`ViewRootIml`的`setView`方法
* 4.`setView`会通过**IPC**最终调用`WindowManagerService`的`addView`方法。
* 5.而`WindowManagerService`的`addView`方法会通过token进行一系列的判断，如果不符合条件则直接return
* 6.`ViewRootIml`的`setView`会根据`IPC`返回的结果，如果不正确，则会抛出异常。
#### Token的创建流程
看了上面的流程我们大体上有了一个概念，就是我们经常遇到的`BadTokenException`其实就是和我们的token有关，那么这里的token是怎么创建的呢？这里我们就要回到刚才的地方。
```
final void attach(Context context, ActivityThread aThread,
            Instrumentation instr, IBinder token, int ident,
            Application application, Intent intent, ActivityInfo info,
            CharSequence title, Activity parent, String id,
            NonConfigurationInstances lastNonConfigurationInstances,
            Configuration config, String referrer, IVoiceInteractor voiceInteractor,
            Window window, ActivityConfigCallback activityConfigCallback) {
        ...
        mToken = token;
       	...

        mWindow.setWindowManager(
                (WindowManager)context.getSystemService(Context.WINDOW_SERVICE),
                mToken, mComponent.flattenToString(),
                (info.flags & ActivityInfo.FLAG_HARDWARE_ACCELERATED) != 0);
        if (mParent != null) {
            mWindow.setContainer(mParent.getWindow());
        }
       	...
    }
```
首先在`Activity`的`attach`方法我们会看到这里Activity保存了传入的token对象，并且还设置给了`PhoneWindow`
然后在调用`WindowManagerGlobal`的`addView`方法的时候、
```
public void addView(View view, ViewGroup.LayoutParams params,
            Display display, Window parentWindow) {
        ...
        final WindowManager.LayoutParams wparams = (WindowManager.LayoutParams) params;
        if (parentWindow != null) {
			//设置token的方法
            parentWindow.adjustLayoutParamsForSubWindow(wparams);
        } else {
            // If there's no parent, then hardware acceleration for this view is
            // set from the application's hardware acceleration setting.
            final Context context = view.getContext();
            if (context != null
                    && (context.getApplicationInfo().flags
                            & ApplicationInfo.FLAG_HARDWARE_ACCELERATED) != 0) {
                wparams.flags |= WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED;
            }
        }
		...
    }
```
这里有一个`parentWindow`的概念
* 1. 如果是应用程序窗口的话，这个parentWindow就是activity的window
* 2. 如果是子窗口的话，这个parentWindow就是activity的window
* 3. 如果是系统窗口的话，那个parentWindow就是null

```
void adjustLayoutParamsForSubWindow(WindowManager.LayoutParams wp) {
        CharSequence curTitle = wp.getTitle();
		//子窗口
        if (wp.type >= WindowManager.LayoutParams.FIRST_SUB_WINDOW &&
                wp.type <= WindowManager.LayoutParams.LAST_SUB_WINDOW) {
            if (wp.token == null) {
                View decor = peekDecorView();
                if (decor != null) {
                    wp.token = decor.getWindowToken();
                }
            }
            ...
        } else if (wp.type >= WindowManager.LayoutParams.FIRST_SYSTEM_WINDOW &&
                wp.type <= WindowManager.LayoutParams.LAST_SYSTEM_WINDOW) {
			//系统类型的Window
            // We don't set the app token to this system window because the life cycles should be
            // independent. If an app creates a system window and then the app goes to the stopped
            // state, the system window should not be affected (can still show and receive input
            // events).
            ...
        } else {
			//应用程序窗口
            if (wp.token == null) {
                wp.token = mContainer == null ? mAppToken : mContainer.mAppToken;
            }
            ...
    }
```
可以看到这里分别针对不同类型的type来进行判断，给`WindowManager.LayoutParams`设置`token`，而设置完`token`到`param`后，这个token就会一直带到我们刚才的流程中，进行判断。那么这里我们就来分别看一下几种类型的`Window`的`token`。
```
public static class LayoutParams extends ViewGroup.LayoutParams
            implements Parcelable {
        //窗口的绝对XY位置，需要考虑gravity属性
        public int x;
        public int y;
        //在横纵方向上为相关的View预留多少扩展像素，如果是0则此view不能被拉伸，其他情况下扩展像素被widget均分
        public float horizontalWeight;
        public float verticalWeight;
        //窗口类型
        //有3种主要类型如下：
        //ApplicationWindows取值在FIRST_APPLICATION_WINDOW与LAST_APPLICATION_WINDOW之间，是常用的顶层应用程序窗口，须将token设置成Activity的token；
        //SubWindows取值在FIRST_SUB_WINDOW和LAST_SUB_WINDOW之间，与顶层窗口相关联，需将token设置成它所附着宿主窗口的token；
        //SystemWindows取值在FIRST_SYSTEM_WINDOW和LAST_SYSTEM_WINDOW之间，不能用于应用程序，使用时需要有特殊权限，它是特定的系统功能才能使用；
        public int type;

        //WindowType：开始应用程序窗口
        public static final int FIRST_APPLICATION_WINDOW = 1;
        //WindowType：所有程序窗口的base窗口，其他应用程序窗口都显示在它上面
        public static final int TYPE_BASE_APPLICATION   = 1;
        //WindowType：普通应用程序窗口，token必须设置为Activity的token来指定窗口属于谁
        public static final int TYPE_APPLICATION        = 2;
        //WindowType：应用程序启动时所显示的窗口，应用自己不要使用这种类型，它被系统用来显示一些信息，直到应用程序可以开启自己的窗口为止
        public static final int TYPE_APPLICATION_STARTING = 3;
        //WindowType：结束应用程序窗口
        public static final int LAST_APPLICATION_WINDOW = 99;

        //WindowType：SubWindows子窗口，子窗口的Z序和坐标空间都依赖于他们的宿主窗口
        public static final int FIRST_SUB_WINDOW        = 1000;
        //WindowType： 面板窗口，显示于宿主窗口的上层
        public static final int TYPE_APPLICATION_PANEL  = FIRST_SUB_WINDOW;
        //WindowType：媒体窗口（例如视频），显示于宿主窗口下层
        public static final int TYPE_APPLICATION_MEDIA  = FIRST_SUB_WINDOW+1;
        //WindowType：应用程序窗口的子面板，显示于所有面板窗口的上层
        public static final int TYPE_APPLICATION_SUB_PANEL = FIRST_SUB_WINDOW+2;
        //WindowType：对话框，类似于面板窗口，绘制类似于顶层窗口，而不是宿主的子窗口
        public static final int TYPE_APPLICATION_ATTACHED_DIALOG = FIRST_SUB_WINDOW+3;
        //WindowType：媒体信息，显示在媒体层和程序窗口之间，需要实现半透明效果
        public static final int TYPE_APPLICATION_MEDIA_OVERLAY  = FIRST_SUB_WINDOW+4;
        //WindowType：子窗口结束
        public static final int LAST_SUB_WINDOW         = 1999;

        //WindowType：系统窗口，非应用程序创建
        public static final int FIRST_SYSTEM_WINDOW     = 2000;
        //WindowType：状态栏，只能有一个状态栏，位于屏幕顶端，其他窗口都位于它下方
        public static final int TYPE_STATUS_BAR         = FIRST_SYSTEM_WINDOW;
        //WindowType：搜索栏，只能有一个搜索栏，位于屏幕上方
        public static final int TYPE_SEARCH_BAR         = FIRST_SYSTEM_WINDOW+1;
        //WindowType：电话窗口，它用于电话交互（特别是呼入），置于所有应用程序之上，状态栏之下
        public static final int TYPE_PHONE              = FIRST_SYSTEM_WINDOW+2;
        //WindowType：系统提示，出现在应用程序窗口之上
        public static final int TYPE_SYSTEM_ALERT       = FIRST_SYSTEM_WINDOW+3;
        //WindowType：锁屏窗口
        public static final int TYPE_KEYGUARD           = FIRST_SYSTEM_WINDOW+4;
        //WindowType：信息窗口，用于显示Toast
        public static final int TYPE_TOAST              = FIRST_SYSTEM_WINDOW+5;
        //WindowType：系统顶层窗口，显示在其他一切内容之上，此窗口不能获得输入焦点，否则影响锁屏
        public static final int TYPE_SYSTEM_OVERLAY     = FIRST_SYSTEM_WINDOW+6;
        //WindowType：电话优先，当锁屏时显示，此窗口不能获得输入焦点，否则影响锁屏
        public static final int TYPE_PRIORITY_PHONE     = FIRST_SYSTEM_WINDOW+7;
        //WindowType：系统对话框
        public static final int TYPE_SYSTEM_DIALOG      = FIRST_SYSTEM_WINDOW+8;
        //WindowType：锁屏时显示的对话框
        public static final int TYPE_KEYGUARD_DIALOG    = FIRST_SYSTEM_WINDOW+9;
        //WindowType：系统内部错误提示，显示于所有内容之上
        public static final int TYPE_SYSTEM_ERROR       = FIRST_SYSTEM_WINDOW+10;
        //WindowType：内部输入法窗口，显示于普通UI之上，应用程序可重新布局以免被此窗口覆盖
        public static final int TYPE_INPUT_METHOD       = FIRST_SYSTEM_WINDOW+11;
        //WindowType：内部输入法对话框，显示于当前输入法窗口之上
        public static final int TYPE_INPUT_METHOD_DIALOG= FIRST_SYSTEM_WINDOW+12;
        //WindowType：墙纸窗口
        public static final int TYPE_WALLPAPER          = FIRST_SYSTEM_WINDOW+13;
        //WindowType：状态栏的滑动面板
        public static final int TYPE_STATUS_BAR_PANEL   = FIRST_SYSTEM_WINDOW+14;
        //WindowType：安全系统覆盖窗口，这些窗户必须不带输入焦点，否则会干扰键盘
        public static final int TYPE_SECURE_SYSTEM_OVERLAY = FIRST_SYSTEM_WINDOW+15;
        //WindowType：拖放伪窗口，只有一个阻力层(最多)，它被放置在所有其他窗口上面
        public static final int TYPE_DRAG               = FIRST_SYSTEM_WINDOW+16;
        //WindowType：状态栏下拉面板
        public static final int TYPE_STATUS_BAR_SUB_PANEL = FIRST_SYSTEM_WINDOW+17;
        //WindowType：鼠标指针
        public static final int TYPE_POINTER = FIRST_SYSTEM_WINDOW+18;
        //WindowType：导航栏(有别于状态栏时)
        public static final int TYPE_NAVIGATION_BAR = FIRST_SYSTEM_WINDOW+19;
        //WindowType：音量级别的覆盖对话框，显示当用户更改系统音量大小
        public static final int TYPE_VOLUME_OVERLAY = FIRST_SYSTEM_WINDOW+20;
        //WindowType：起机进度框，在一切之上
        public static final int TYPE_BOOT_PROGRESS = FIRST_SYSTEM_WINDOW+21;
        //WindowType：假窗，消费导航栏隐藏时触摸事件
        public static final int TYPE_HIDDEN_NAV_CONSUMER = FIRST_SYSTEM_WINDOW+22;
        //WindowType：梦想(屏保)窗口，略高于键盘
        public static final int TYPE_DREAM = FIRST_SYSTEM_WINDOW+23;
        //WindowType：导航栏面板(不同于状态栏的导航栏)
        public static final int TYPE_NAVIGATION_BAR_PANEL = FIRST_SYSTEM_WINDOW+24;
        //WindowType：universe背后真正的窗户
        public static final int TYPE_UNIVERSE_BACKGROUND = FIRST_SYSTEM_WINDOW+25;
        //WindowType：显示窗口覆盖，用于模拟辅助显示设备
        public static final int TYPE_DISPLAY_OVERLAY = FIRST_SYSTEM_WINDOW+26;
        //WindowType：放大窗口覆盖，用于突出显示的放大部分可访问性放大时启用
        public static final int TYPE_MAGNIFICATION_OVERLAY = FIRST_SYSTEM_WINDOW+27;
        //WindowType：......
        public static final int TYPE_KEYGUARD_SCRIM           = FIRST_SYSTEM_WINDOW+29;
        public static final int TYPE_PRIVATE_PRESENTATION = FIRST_SYSTEM_WINDOW+30;
        public static final int TYPE_VOICE_INTERACTION = FIRST_SYSTEM_WINDOW+31;
        public static final int TYPE_ACCESSIBILITY_OVERLAY = FIRST_SYSTEM_WINDOW+32;
        //WindowType：系统窗口结束
        public static final int LAST_SYSTEM_WINDOW      = 2999;

        //MemoryType：窗口缓冲位于主内存
        public static final int MEMORY_TYPE_NORMAL = 0;
        //MemoryType：窗口缓冲位于可以被DMA访问，或者硬件加速的内存区域
        public static final int MEMORY_TYPE_HARDWARE = 1;
        //MemoryType：窗口缓冲位于可被图形加速器访问的区域
        public static final int MEMORY_TYPE_GPU = 2;
        //MemoryType：窗口缓冲不拥有自己的缓冲区，不能被锁定，缓冲区由本地方法提供
        public static final int MEMORY_TYPE_PUSH_BUFFERS = 3;

        //指出窗口所使用的内存缓冲类型，默认为NORMAL 
        public int memoryType;

        //Flag：当该window对用户可见的时候，允许锁屏
        public static final int FLAG_ALLOW_LOCK_WHILE_SCREEN_ON     = 0x00000001;
        //Flag：让该window后所有的东西都成暗淡
        public static final int FLAG_DIM_BEHIND        = 0x00000002;
        //Flag：让该window后所有东西都模糊（4.0以上已经放弃这种毛玻璃效果）
        public static final int FLAG_BLUR_BEHIND        = 0x00000004;
        //Flag：让window不能获得焦点，这样用户快就不能向该window发送按键事
        public static final int FLAG_NOT_FOCUSABLE      = 0x00000008;
        //Flag：让该window不接受触摸屏事件
        public static final int FLAG_NOT_TOUCHABLE      = 0x00000010;
        //Flag：即使在该window在可获得焦点情况下，依旧把该window之外的任何event发送到该window之后的其他window
        public static final int FLAG_NOT_TOUCH_MODAL    = 0x00000020;
        //Flag：当手机处于睡眠状态时，如果屏幕被按下，那么该window将第一个收到
        public static final int FLAG_TOUCHABLE_WHEN_WAKING = 0x00000040;
        //Flag：当该window对用户可见时，让设备屏幕处于高亮（bright）状态
        public static final int FLAG_KEEP_SCREEN_ON     = 0x00000080;
        //Flag：让window占满整个手机屏幕，不留任何边界
        public static final int FLAG_LAYOUT_IN_SCREEN   = 0x00000100;
        //Flag：window大小不再不受手机屏幕大小限制，即window可能超出屏幕之外
        public static final int FLAG_LAYOUT_NO_LIMITS   = 0x00000200;
        //Flag：window全屏显示
        public static final int FLAG_FULLSCREEN      = 0x00000400;
        //Flag：恢复window非全屏显示
        public static final int FLAG_FORCE_NOT_FULLSCREEN   = 0x00000800;
        //Flag：开启抖动（dithering）
        public static final int FLAG_DITHER             = 0x00001000;
        //Flag：当该window在进行显示的时候，不允许截屏
        public static final int FLAG_SECURE             = 0x00002000;
        //Flag：一个特殊模式的布局参数用于执行扩展表面合成时到屏幕上
        public static final int FLAG_SCALED             = 0x00004000;
        //Flag：用于windows时,经常会使用屏幕用户持有反对他们的脸,它将积极过滤事件流,以防止意外按在这种情况下,可能不需要为特定的窗口,在检测到这样一个事件流时,应用程序将接收取消运动事件表明,这样应用程序可以处理这相应地采取任何行动的事件,直到手指释放
        public static final int FLAG_IGNORE_CHEEK_PRESSES    = 0x00008000;
        //Flag：一个特殊的选项只用于结合FLAG_LAYOUT_IN_SC
        public static final int FLAG_LAYOUT_INSET_DECOR = 0x00010000;
        //Flag：转化的状态FLAG_NOT_FOCUSABLE对这个窗口当前如何进行交互的方法
        public static final int FLAG_ALT_FOCUSABLE_IM = 0x00020000;
        //Flag：如果你设置了该flag,那么在你FLAG_NOT_TOUNCH_MODAL的情况下，即使触摸屏事件发送在该window之外，其事件被发送到了后面的window,那么该window仍然将以MotionEvent.ACTION_OUTSIDE形式收到该触摸屏事件
        public static final int FLAG_WATCH_OUTSIDE_TOUCH = 0x00040000;
        //Flag：当锁屏的时候，显示该window
        public static final int FLAG_SHOW_WHEN_LOCKED = 0x00080000;
        //Flag：在该window后显示系统的墙纸
        public static final int FLAG_SHOW_WALLPAPER = 0x00100000;
        //Flag：当window被显示的时候，系统将把它当做一个用户活动事件，以点亮手机屏幕
        public static final int FLAG_TURN_SCREEN_ON = 0x00200000;
        //Flag：消失键盘
        public static final int FLAG_DISMISS_KEYGUARD = 0x00400000;
        //Flag：当该window在可以接受触摸屏情况下，让因在该window之外，而发送到后面的window的触摸屏可以支持split touch
        public static final int FLAG_SPLIT_TOUCH = 0x00800000;
        //Flag：对该window进行硬件加速，该flag必须在Activity或Dialog的Content View之前进行设置
        public static final int FLAG_HARDWARE_ACCELERATED = 0x01000000;
        //Flag：让window占满整个手机屏幕，不留任何边界
        public static final int FLAG_LAYOUT_IN_OVERSCAN = 0x02000000;
        //Flag：请求一个半透明的状态栏背景以最小的系统提供保护
        public static final int FLAG_TRANSLUCENT_STATUS = 0x04000000;
        //Flag：请求一个半透明的导航栏背景以最小的系统提供保护
        public static final int FLAG_TRANSLUCENT_NAVIGATION = 0x08000000;
        //Flag：......
        public static final int FLAG_LOCAL_FOCUS_MODE = 0x10000000;
        public static final int FLAG_SLIPPERY = 0x20000000;
        public static final int FLAG_LAYOUT_ATTACHED_IN_DECOR = 0x40000000;
        public static final int FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS = 0x80000000;

        //行为选项标记
        public int flags;

        //PrivateFlags：......
        public static final int PRIVATE_FLAG_FAKE_HARDWARE_ACCELERATED = 0x00000001;
        public static final int PRIVATE_FLAG_FORCE_HARDWARE_ACCELERATED = 0x00000002;
        public static final int PRIVATE_FLAG_WANTS_OFFSET_NOTIFICATIONS = 0x00000004;
        public static final int PRIVATE_FLAG_SHOW_FOR_ALL_USERS = 0x00000010;
        public static final int PRIVATE_FLAG_NO_MOVE_ANIMATION = 0x00000040;
        public static final int PRIVATE_FLAG_COMPATIBLE_WINDOW = 0x00000080;
        public static final int PRIVATE_FLAG_SYSTEM_ERROR = 0x00000100;
        public static final int PRIVATE_FLAG_INHERIT_TRANSLUCENT_DECOR = 0x00000200;
        public static final int PRIVATE_FLAG_KEYGUARD = 0x00000400;
        public static final int PRIVATE_FLAG_DISABLE_WALLPAPER_TOUCH_EVENTS = 0x00000800;

        //私有的行为选项标记
        public int privateFlags;

        public static final int NEEDS_MENU_UNSET = 0;
        public static final int NEEDS_MENU_SET_TRUE = 1;
        public static final int NEEDS_MENU_SET_FALSE = 2;
        public int needsMenuKey = NEEDS_MENU_UNSET;

        public static boolean mayUseInputMethod(int flags) {
            ......
        }

        //SOFT_INPUT：用于描述软键盘显示规则的bite的mask
        public static final int SOFT_INPUT_MASK_STATE = 0x0f;
        //SOFT_INPUT：没有软键盘显示的约定规则
        public static final int SOFT_INPUT_STATE_UNSPECIFIED = 0;
        //SOFT_INPUT：可见性状态softInputMode，请不要改变软输入区域的状态
        public static final int SOFT_INPUT_STATE_UNCHANGED = 1;
        //SOFT_INPUT：用户导航（navigate）到你的窗口时隐藏软键盘
        public static final int SOFT_INPUT_STATE_HIDDEN = 2;
        //SOFT_INPUT：总是隐藏软键盘
        public static final int SOFT_INPUT_STATE_ALWAYS_HIDDEN = 3;
        //SOFT_INPUT：用户导航（navigate）到你的窗口时显示软键盘
        public static final int SOFT_INPUT_STATE_VISIBLE = 4;
        //SOFT_INPUT：总是显示软键盘
        public static final int SOFT_INPUT_STATE_ALWAYS_VISIBLE = 5;
        //SOFT_INPUT：显示软键盘时用于表示window调整方式的bite的mask
        public static final int SOFT_INPUT_MASK_ADJUST = 0xf0;
        //SOFT_INPUT：不指定显示软件盘时，window的调整方式
        public static final int SOFT_INPUT_ADJUST_UNSPECIFIED = 0x00;
        //SOFT_INPUT：当显示软键盘时，调整window内的控件大小以便显示软键盘
        public static final int SOFT_INPUT_ADJUST_RESIZE = 0x10;
        //SOFT_INPUT：当显示软键盘时，调整window的空白区域来显示软键盘，即使调整空白区域，软键盘还是有可能遮挡一些有内容区域，这时用户就只有退出软键盘才能看到这些被遮挡区域并进行
        public static final int SOFT_INPUT_ADJUST_PAN = 0x20;
        //SOFT_INPUT：当显示软键盘时，不调整window的布局
        public static final int SOFT_INPUT_ADJUST_NOTHING = 0x30;
        //SOFT_INPUT：用户导航（navigate）到了你的window
        public static final int SOFT_INPUT_IS_FORWARD_NAVIGATION = 0x100;

        //软输入法模式选项
        public int softInputMode;

        //窗口如何停靠
        public int gravity;
        //水平边距，容器与widget之间的距离，占容器宽度的百分率
        public float horizontalMargin;
        //纵向边距
        public float verticalMargin;
        //积极的insets绘图表面和窗口之间的内容
        public final Rect surfaceInsets = new Rect();
        //期望的位图格式，默认为不透明，参考android.graphics.PixelFormat
        public int format;
        //窗口所使用的动画设置，它必须是一个系统资源而不是应用程序资源，因为窗口管理器不能访问应用程序
        public int windowAnimations;
        //整个窗口的半透明值，1.0表示不透明，0.0表示全透明
        public float alpha = 1.0f;
        //当FLAG_DIM_BEHIND设置后生效，该变量指示后面的窗口变暗的程度，1.0表示完全不透明，0.0表示没有变暗
        public float dimAmount = 1.0f;

        public static final float BRIGHTNESS_OVERRIDE_NONE = -1.0f;
        public static final float BRIGHTNESS_OVERRIDE_OFF = 0.0f;
        public static final float BRIGHTNESS_OVERRIDE_FULL = 1.0f;
        public float screenBrightness = BRIGHTNESS_OVERRIDE_NONE;
        //用来覆盖用户设置的屏幕亮度，表示应用用户设置的屏幕亮度，从0到1调整亮度从暗到最亮发生变化
        public float buttonBrightness = BRIGHTNESS_OVERRIDE_NONE;

        public static final int ROTATION_ANIMATION_ROTATE = 0;
        public static final int ROTATION_ANIMATION_CROSSFADE = 1;
        public static final int ROTATION_ANIMATION_JUMPCUT = 2;
        //定义出入境动画在这个窗口旋转设备时使用
        public int rotationAnimation = ROTATION_ANIMATION_ROTATE;

        //窗口的标示符
        public IBinder token = null;
        //此窗口所在的包名
        public String packageName = null;
        //屏幕方向
        public int screenOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED;
        //首选的刷新率的窗口
        public float preferredRefreshRate;
        //控制status bar是否显示
        public int systemUiVisibility;
        //ui能见度所请求的视图层次结构
        public int subtreeSystemUiVisibility;
        //得到关于系统ui能见度变化的回调
        public boolean hasSystemUiListeners;

        public static final int INPUT_FEATURE_DISABLE_POINTER_GESTURES = 0x00000001;
        public static final int INPUT_FEATURE_NO_INPUT_CHANNEL = 0x00000002;
        public static final int INPUT_FEATURE_DISABLE_USER_ACTIVITY = 0x00000004;
        public int inputFeatures;
        public long userActivityTimeout = -1;

        ......
        public final int copyFrom(LayoutParams o) {
            ......
        }

        ......
        public void scale(float scale) {
            ......
        }

        ......
    }
```
[引用翻译](https://blog.csdn.net/yanbober/java/article/details/46361191)
#### Dialog
首先关于`Dialog`的原理可以参考我原来的一篇文章[【Window系列】——Dialog源码解析](https://www.jianshu.com/p/7874bfb20ca0),这里面的最后有提到，**为什么我们创建Dialog传入的Context必须是Activity类型的**，这里我们看下`Dialog`的创建过程。
```
Dialog(@NonNull Context context, @StyleRes int themeResId, boolean createContextThemeWrapper) {
        ...
		//获取Activity的WindowManager
        mWindowManager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
		//创建自己的PhoneWindow
        final Window w = new PhoneWindow(mContext);
        mWindow = w;
        w.setCallback(this);
        w.setOnWindowDismissedCallback(this);
        w.setOnWindowSwipeDismissedCallback(() -> {
            if (mCancelable) {
                cancel();
            }
        });
		//设置windowManger，注意后面两个参数为null
        w.setWindowManager(mWindowManager, null, null);
        w.setGravity(Gravity.CENTER);

        mListenersHandler = new ListenersHandler(this);
    }
```
这里假定我们传入的是`Activity`类型的Context，前面我们有讲到
```
@Override
    public Object getSystemService(@ServiceName @NonNull String name) {
        ...
        if (WINDOW_SERVICE.equals(name)) {
            return mWindowManager;
        } else if (SEARCH_SERVICE.equals(name)) {
            ensureSearchManager();
            return mSearchManager;
        }
        return super.getSystemService(name);
    }
```
这里就会返回`Activity`内部的`WindowManager`了，然后Dialog自己创建了`Window`对象，也就是说`Dialog`是和`Activity`**共用一个WindowManager，但Window不同**
```
public void setWindowManager(WindowManager wm, IBinder appToken, String appName) {
        setWindowManager(wm, appToken, appName, false);
    }
```
而`setWindowManager`方法里的入参可以看到，在`Dialog`的这里传入的`token`是null。
我们继续看`Dialog`的`show`方法。
```
public void show() {
        ...
        onStart();
        mDecor = mWindow.getDecorView();

       ..
        WindowManager.LayoutParams l = mWindow.getAttributes();
       ...
        mWindowManager.addView(mDecor, l);
        mShowing = true;

        sendShowMessage();
    }
```
看到我们刚才分析到的用于保存`token`对象和`type`类型的`WindowManager.LayoutParams`。
```
Window.java

// The current window attributes.
    private final WindowManager.LayoutParams mWindowAttributes =
        new WindowManager.LayoutParams();

public final WindowManager.LayoutParams getAttributes() {
        return mWindowAttributes;
    }
```
因为我们刚才分析知道，`Dialog`是自己本身创建了一个新的`PhoneWindow`,所以可以看到`WindowManager.LayoutParams`用的是默认值。
```
public LayoutParams() {
            super(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT);
            type = TYPE_APPLICATION;
            format = PixelFormat.OPAQUE;
        }
```
总算看到了`type`对象，所以我们可以得出一个结论：
**Dialog是应用程序类型的Window**
再结合我们上面的结论:**应用程序类型的parentWindow不为空，并且使用的是parentWindow的token**
这里一下就很清晰了，`Dialog`在执行`mWindowManager.addView(mDecor, l);`方法时，由于`Context`使用的是`Activity`，所以`WindowManager`用的是`Activity`的`WindowManager`，而`Activity`的`WindowManger`保存了`Activity`的`token`,所以就能正常添加了，如果使用的不是`Activity`，而是`Application`，那么就会由于没有`token`对象，而抛异常。
#### Toast
首先关于`Toast`的原理可以参考我原来的一篇文章[【Window系列】——Toast源码解析
](https://www.jianshu.com/p/f9e60e9272cf)，这里面同样提到了关于`token`的疑问，所以我们带着结论来看下
```
TN(String packageName, @Nullable Looper looper) {
            // XXX This should be changed to use a Dialog, with a Theme.Toast
            // defined that sets up the layout params appropriately.
            final WindowManager.LayoutParams params = mParams;
           	...
			//设置为系统类型的
            params.type = WindowManager.LayoutParams.TYPE_TOAST;
			...
}
public void handleShow(IBinder windowToken) {
            if (localLOGV) Log.v(TAG, "HANDLE SHOW: " + this + " mView=" + mView
                    + " mNextView=" + mNextView);
            // If a cancel/hide is pending - no need to show - at this point
            // the window token is already invalid and no need to do any work.
            if (mHandler.hasMessages(CANCEL) || mHandler.hasMessages(HIDE)) {
                return;
            }
            if (mView != mNextView) {
                // remove the old view if necessary
                handleHide();
                mView = mNextView;
				//context
                Context context = mView.getContext().getApplicationContext();
                String packageName = mView.getContext().getOpPackageName();
                if (context == null) {
                    context = mView.getContext();
                }
                mWM = (WindowManager)context.getSystemService(Context.WINDOW_SERVICE);
                ...
                    //设置token
                mParams.token = windowToken;
                if (mView.getParent() != null) {
                    if (localLOGV) Log.v(TAG, "REMOVE! " + mView + " in " + this);
                    mWM.removeView(mView);
                }
                if (localLOGV) Log.v(TAG, "ADD! " + mView + " in " + this);
                // Since the notification manager service cancels the token right
                // after it notifies us to cancel the toast there is an inherent
                // race and we may attempt to add a window after the token has been
                // invalidated. Let us hedge against that.
                try {
                //利用WindowManager将View加入
                    mWM.addView(mView, mParams);
                    trySendAccessibilityEvent();
                } catch (WindowManager.BadTokenException e) {
                    /* ignore */
                }
            }
        }
```
这里可以看到首先在`TN`对象的创建方法里面，将`WindowManager.LayoutParams`设置为了`WindowManager.LayoutParams.TYPE_TOAST`系统类型，而对于刚才的结论可以得到，系统类型的`token`为null也是可以正常显示的，所以在`WindowManager`的获取地方，可以看到这里获取的是`Application`类型的，也就是`WindowManager`为新创建的，并且`token`为null。
##### Toast的`BadTokenException`
这里要说下，由于`Toast`的版本差异，导致我们在一些版本的Toast，会有关闭权限通知导致无法显示`Toast`的问题，分析原因是在某个版本，系统源码对于`WindowManager.LayoutParams.TYPE_TOAST`做了权限控制，所以没有系统通知权限的时候，`Toast`也无法正常显示，这里有些地方的解决方式是手动传入`Toast`的`WindowManager.LayoutParams`，不再使用`WindowManager.LayoutParams.TYPE_TOAST`这样确实能避免关闭通知权限无法显示的问题，但是就会出现几个问题：
1.`Toast`由于不是系统类型的，所以依赖于父布局，所以不再支持Activity跳转时仍然显示
2.由于`Toast`变成了不是系统类型，依赖父布局，所以就可能在某些`Activity`销毁的生命周期内显示`Toast`就会有`BadTokenException`
#### PopupWindow
首先关于`PopupWindow`的原理可以参考我原来的一篇文章[【Window系列】——PopupWindow的前世今生](https://www.jianshu.com/p/9dafea9cb3c0)
有了前面的经验，我们知道了分析一个弹窗类型的分析三步：
>1.先分析`WindowManager`是不是`Activity`公用
>2.再分析`WindowManager.LayoutParams`的type类型
>3.最后分析`WindowManager.LayoutParams`的token赋值
所以我们来看下`PopupWindow`的
```
public PopupWindow(View contentView, int width, int height, boolean focusable) {
        if (contentView != null) {
            mContext = contentView.getContext();
			//传入的View的Context类型，
            mWindowManager = (WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE);
        }

        setContentView(contentView);
        setWidth(width);
        setHeight(height);
        setFocusable(focusable);
    }
```
首先可以看到`PopupWindow`使用的是传入View的`Context`，一般我们传入的都是我们布局里面的某一个View，所以这里`Context`对象就是`Activity`，所以可以得到**是Activity共用的WindowManager**
```
//子布局类型
private int mWindowLayoutType = WindowManager.LayoutParams.TYPE_APPLICATION_PANEL;
public void showAsDropDown(View anchor, int xoff, int yoff, int gravity) {
        ...
        //创建布局参数
        final WindowManager.LayoutParams p =
                createPopupLayoutParams(anchor.getApplicationWindowToken());
        ...
    }
protected final WindowManager.LayoutParams createPopupLayoutParams(IBinder token) {
        final WindowManager.LayoutParams p = new WindowManager.LayoutParams();
		...
        p.type = mWindowLayoutType;
        p.token = token;
        ...
        return p;
    }
```
然后可以看到创建`WindowManager.LayoutParams`,传入了依赖的`View`的`token`，也就是`parentView`的`token`，并且`type`是`WindowManager.LayoutParams.TYPE_APPLICATION_PANEL;`子布局类型，所以符合预期，可以正常显示的。
### 总结
WindowManager.LayoutParams中分为三种类型

**应用程序窗口** : type在 FIRST_APPLICATION_WINDOW ~ LAST_APPLICATION_WINDOW 之间
要求：**token设置成Activity的token。**  
例如：Dialog

**子窗口**: type在 FIRST_SUB_WINDOW ~ LAST_SUB_WINDOW SubWindows之间  
要求：**需将token设置成它所附着宿主窗口的token。**
例如：PopupWindow(想要依附在Activity上需要将token设置成Activity的token)

**系统窗口**: type值在 FIRST_SYSTEM_WINDOW ~ LAST_SYSTEM_WINDOW之间。
要求：token可以为null，但需要权限运行才能使用
例如: Toast，输入法等。

分析一个弹窗类型的分析三步：
>1.先分析`WindowManager`是不是`Activity`公用
>2.再分析`WindowManager.LayoutParams`的type类型
>3.最后分析`WindowManager.LayoutParams`的token赋值

### 相关文章推荐
1.[Android应用Activity、Dialog、PopWindow、Toast窗口添加机制及源码分析](https://blog.csdn.net/yanbober/article/details/46361191)
2.[Android窗口机制（五）最终章：WindowManager.LayoutParams和Token以及其他窗口Dialog，Toast](https://www.jianshu.com/p/bac61386d9bf)
3.[Toast通知栏权限填坑指南](https://www.jianshu.com/p/1d64a5ccbc7c)
4.[同学，你的系统Toast可能需要修复一下](https://juejin.im/post/5c05f011e51d451b802586c6)
5.[创建Dialog所需的上下文为什么必须是Activity？
](https://www.jianshu.com/p/413ec659500a)6.[WindowManager调用流程源码分析
](https://juejin.im/post/5abdf406518825556e5e3451)7.[Android之Window和弹窗问题
](https://www.jianshu.com/p/1a40029ffe35?utm_source=desktop&utm_medium=timeline)8.[Toast与Snackbar的那点事](https://tech.meituan.com/2018/03/29/toast-snackbar-replace.html)
