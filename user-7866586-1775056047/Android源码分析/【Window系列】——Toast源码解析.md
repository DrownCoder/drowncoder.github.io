>本系列博客基于android-28版本
[【Window系列】——Toast源码解析](https://www.jianshu.com/p/f9e60e9272cf)
[【Window系列】——PopupWindow的前世今生](https://www.jianshu.com/p/9dafea9cb3c0)
[【Window系列】——Dialog源码解析](https://www.jianshu.com/p/7874bfb20ca0)
[【Window系列】——Window中的Token](https://www.jianshu.com/p/3411ee4cb739)
### 前言
Toast组件应该是接触Android中使用率非常高的一个原生控件，其使用的便捷性一直是开发者选用的原因，短短的一行代码就可以实现支持跨页面的提示功能。但是随着Google对于Android系统自身安全性的限制，导致Toast组件目前在高版本上也出现了许多问题，例如当关闭应用的通知栏权限，全局的Toast就无法展示了。本期博客就先从源码角度分析Toast的实现原理，只有了解了Toast的实现原理，才能想办法解决问题。
### 源码解析
我们使用Toast一般的使用方式如下：
`Toast.makeText(context, message, Toast.LENGTH_SHORT).show();`
所以我们来分别看一下两个方法。
```
/**
     * Make a standard toast that just contains a text view.
     *
     * @param context  The context to use.  Usually your {@link android.app.Application}
     *                 or {@link android.app.Activity} object.
     * @param text     The text to show.  Can be formatted text.
     * @param duration How long to display the message.  Either {@link #LENGTH_SHORT} or
     *                 {@link #LENGTH_LONG}
     *
     */
    public static Toast makeText(Context context, CharSequence text, @Duration int duration) {
        return makeText(context, null, text, duration);
    }
    public static Toast makeText(@NonNull Context context, @Nullable Looper looper,
            @NonNull CharSequence text, @Duration int duration) {
        Toast result = new Toast(context, looper);

        LayoutInflater inflate = (LayoutInflater)
                context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
        View v = inflate.inflate(com.android.internal.R.layout.transient_notification, null);
        TextView tv = (TextView)v.findViewById(com.android.internal.R.id.message);
        tv.setText(text);

        result.mNextView = v;
        result.mDuration = duration;

        return result;
    }
```
这里有两个注意点：
1.可以看到这里注释写到了，延时`duration`只能是变量`LENGTH_SHORT `或`LENGTH_LONG `具体原因后面源码分析到再看。
2.我们每次使用Toast都会new一个新的Toast对象，而这个布局就是一个`transient_notification.xml`文件
现在首先来看一下Toast的构造函数
```
public Toast(@NonNull Context context, @Nullable Looper looper) {
        mContext = context;
        mTN = new TN(context.getPackageName(), looper);
        mTN.mY = context.getResources().getDimensionPixelSize(
                com.android.internal.R.dimen.toast_y_offset);
        mTN.mGravity = context.getResources().getInteger(
                com.android.internal.R.integer.config_toastDefaultGravity);
    }
```
可以看到这里创建了一个`TN`对象，这个`TN`后面会贯穿整个Toast的使用全过程，所以我们先看一下这是个什么对象。
```
private static class TN extends ITransientNotification.Stub {
	TN(String packageName, @Nullable Looper looper) {
            // XXX This should be changed to use a Dialog, with a Theme.Toast
            // defined that sets up the layout params appropriately.
            final WindowManager.LayoutParams params = mParams;
            params.height = WindowManager.LayoutParams.WRAP_CONTENT;
            params.width = WindowManager.LayoutParams.WRAP_CONTENT;
            params.format = PixelFormat.TRANSLUCENT;
            params.windowAnimations = com.android.internal.R.style.Animation_Toast;
            //type为TYPE_TOAST类型
            params.type = WindowManager.LayoutParams.TYPE_TOAST;
            params.setTitle("Toast");
            params.flags = WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                    | WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                    | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE;

            mPackageName = packageName;

            if (looper == null) {
                // Use Looper.myLooper() if looper is not specified.
                //获取Looper对象
                looper = Looper.myLooper();
                //如果自线程，没有创建Looper对象，则抛异常
                if (looper == null) {
                    throw new RuntimeException(
                            "Can't toast on a thread that has not called Looper.prepare()");
                }
            }
            //创建Handler对象
            mHandler = new Handler(looper, null) {
                @Override
                public void handleMessage(Message msg) {
                    switch (msg.what) {
                        case SHOW: {
                            IBinder token = (IBinder) msg.obj;
                            handleShow(token);
                            break;
                        }
                        case HIDE: {
                            handleHide();
                            // Don't do this in handleHide() because it is also invoked by
                            // handleShow()
                            mNextView = null;
                            break;
                        }
                        case CANCEL: {
                            handleHide();
                            // Don't do this in handleHide() because it is also invoked by
                            // handleShow()
                            mNextView = null;
                            try {
                                getService().cancelToast(mPackageName, TN.this);
                            } catch (RemoteException e) {
                            }
                            break;
                        }
                    }
                }
            };
        }
}
```
首先可以看到这个TN对象**继承**了`ITransientNotification.Stub`，看到这个名字，如果了解过AIDL机制的话，或者了解过Binder机制的，应该对这个名字很熟悉，这个不就是AIDL的实现类，所以可以看出Toast机制的底层实现肯定用到了Binder机制。可以看到这里面有两个方法被`@Override`标记，`show()`方法和`hide()`方法，这不是正好和我们的显示和隐藏对应吗。
这里我注释着重写了几个点
1.首先可以看到这里创建了`WindowManager.LayoutParams`对象，并且设置了一系列熟悉，其中比较重要的一个是，这里设置了一个`type`属性为`TYPE_TOAST`，这个标记了这个Window的类型，而关闭通知栏权限导致Toast无法展示也是和这个属性有关，不影响本次原理分析，所以暂不分析。
2.获取Looper对象，如果属性Handler机制的话，应该看到这个方法很熟悉，`Looper.myLooper()`这个方法底层利用ThreadLocal获取Looper对象，而一般我们使用Toast都是在主线程使用，主线程的main方法，已经自动完成了Looper.prepare()方法和Looper.loop()方法，
所以已经自动完成了Looper的创建。这里可以看到，如果没有获取到Looper对象，则会抛出异常。所以这里我们也可以对应分析一个问题：
>自线程使用Toast对象会怎么样？

如果熟悉Handler机制的话，应该立马能得出答案，当然是崩溃了，犹豫创建出来的自线程没有创建Looper对象，所以这里无法获取到Looper对象，那么就会抛异常，导致崩溃。
>那么自线程如何使用Toast呢？

还是Handler机制，既然没有Looper机制，那么就创建咯
```
new Thread(){
        public void run(){
          Looper.prepare();//给当前线程初始化Looper
          Toast.makeText(getApplicationContext(),"自线程Toast",0).show();//Toast初始化的时候会new Handler();无参构造默认获取当前线程的Looper，如果没有prepare过，则抛出题主描述的异常。上一句代码初始化过了，就不会出错。
          Looper.loop();//这句执行，Toast排队show所依赖的Handler发出的消息就有人处理了，Toast就可以吐出来了。但是，这个Thread也阻塞这里了，因为loop()是个for (;;) ...
        }
  }.start();

```
3.后面就创建了Handler对象，所以如果是常规情况，那么在Handler中执行的应该是主线程的方法。

看完了构造函数，现在我们就来看一下Toast的`show()`方法
```
public void show() {
        if (mNextView == null) {
            throw new RuntimeException("setView must have been called");
        }

        INotificationManager service = getService();
        String pkg = mContext.getOpPackageName();
        TN tn = mTN;
        tn.mNextView = mNextView;

        try {
            service.enqueueToast(pkg, tn, mDuration);
        } catch (RemoteException e) {
            // Empty
        }
    }

static private INotificationManager getService() {
        if (sService != null) {
            return sService;
        }
        sService = INotificationManager.Stub.asInterface(ServiceManager.getService("notification"));
        return sService;
    }
```
果然和上面分析的一样，这里首先利用Binder获取了`NotificationManagerService`的代理，然后调用了它的`enqueueToast()`方法，注意这里将刚才创建的`TN`对象传了过去，果然是利用了Binder，双向通信。
```
private final IBinder mService = new INotificationManager.Stub() {
        // Toasts
        // ============================================================================

        @Override
        public void enqueueToast(String pkg, ITransientNotification callback, int duration)
        {
            if (DBG) {
                Slog.i(TAG, "enqueueToast pkg=" + pkg + " callback=" + callback
                        + " duration=" + duration);
            }

            if (pkg == null || callback == null) {
                Slog.e(TAG, "Not doing toast. pkg=" + pkg + " callback=" + callback);
                return ;
            }
            final boolean isSystemToast = isCallerSystemOrPhone() || ("android".equals(pkg));
            final boolean isPackageSuspended =
                    isPackageSuspendedForUser(pkg, Binder.getCallingUid());

            if (ENABLE_BLOCKED_TOASTS && !isSystemToast &&
                    (!areNotificationsEnabledForPackage(pkg, Binder.getCallingUid())
                            || isPackageSuspended)) {
                Slog.e(TAG, "Suppressing toast from package " + pkg
                        + (isPackageSuspended
                                ? " due to package suspended by administrator."
                                : " by user request."));
                return;
            }

            synchronized (mToastQueue) {
                int callingPid = Binder.getCallingPid();
                long callingId = Binder.clearCallingIdentity();
                try {
                    ToastRecord record;
                    int index;
                    // All packages aside from the android package can enqueue one toast at a time
                    //是否是系统应用
                    if (!isSystemToast) {
                        index = indexOfToastPackageLocked(pkg);
                    } else {
                        index = indexOfToastLocked(pkg, callback);
                    }

                    // If the package already has a toast, we update its toast
                    // in the queue, we don't move it to the end of the queue.
                    if (index >= 0) {
                    //如果当前队列里已经有Toast，直接更新
                        record = mToastQueue.get(index);
                        record.update(duration);
                        try {
                            record.callback.hide();
                        } catch (RemoteException e) {
                        }
                        record.update(callback);
                    } else {
                    //没有，则创建新的ToastRecord
                        Binder token = new Binder();
                    //生成一个Toast窗口，并且传递token等参数
                        mWindowManagerInternal.addWindowToken(token, TYPE_TOAST, DEFAULT_DISPLAY);
                        //生产一个ToastRecord
                        record = new ToastRecord(callingPid, pkg, callback, duration, token);
                        //将Toast加入队列
                        mToastQueue.add(record);
                        index = mToastQueue.size() - 1;
                    }
                    //设置当前进程为前台进程
                    keepProcessAliveIfNeededLocked(callingPid);
                    // If it's at index 0, it's the current toast.  It doesn't matter if it's
                    // new or just been updated.  Call back and tell it to show itself.
                    // If the callback fails, this will remove it from the list, so don't
                    // assume that it's valid after this.
                    if (index == 0) {
                    //如果当前Toast为队头，则显示Toast
                        showNextToastLocked();
                    }
                } finally {
                    Binder.restoreCallingIdentity(callingId);
                }
            }
        }
```
可以看到，果然利用了Binder，这里首先用`isSystemToast `判断了是否是系统应用
```
final boolean isSystemToast = isCallerSystemOrPhone() || ("android".equals(pkg));
```
可以看到这里，两个判断条件一个是通过进程Id判断是否是系统进程，一个是通过包名判断是否`"android"`，所以后面会的博客会介绍一种通过伪造包名的方式，以系统Toast的方式弹Toast。
后面在定位Toast在队列中的位置的时候，如果队列中已经存在Toast的话，走的就是更新流程，而如果是一个新的Toast，则会首先**创建一个Binder对象**，然后生成一个`ToastRecord`对象，并加入队列，这里注意创建的`Token`对象会被保存在`ToastRecord`对象中。
接下来这个函数很重要：
```
void keepProcessAliveIfNeededLocked(int pid)
    {
        int toastCount = 0; // toasts from this pid
        ArrayList<ToastRecord> list = mToastQueue;
        int N = list.size();
        for (int i=0; i<N; i++) {
            ToastRecord r = list.get(i);
            if (r.pid == pid) {
                toastCount++;
            }
        }
        try {
            mAm.setProcessImportant(mForegroundToken, pid, toastCount > 0, "toast");
        } catch (RemoteException e) {
            // Shouldn't happen.
        }
    }
```
这里将当前弹Toast的进程设置为了前台进程，熟悉Toast的应该都知道，Toast的特殊性在于它支持跨页面显示，甚至当应用关闭的时候，Toast仍然能够展示，就是这个函数发挥的作用，这里利用AMS，还是通过Binder，调用了`setProcessImportant`，将Toast所在的进程设置为了前台进程，保证了进程的存活，所以当页面销毁了，Toast还是可以正常显示。
```
if (index == 0) {
                //如果当前Toast为队头，则显示Toast
                    showNextToastLocked();
                }


void showNextToastLocked() {
		//取出队列头的Toast
        ToastRecord record = mToastQueue.get(0);
        //居然是个循环
        while (record != null) {
            if (DBG) Slog.d(TAG, "Show pkg=" + record.pkg + " callback=" + record.callback);
            try {
            		//调用callback的show方法，传入刚才创建的Token对象
                record.callback.show(record.token);
                //延时移除Toast
                scheduleDurationReachedLocked(record);
                return;
            } catch (RemoteException e) {
                Slog.w(TAG, "Object died trying to show notification " + record.callback
                        + " in package " + record.pkg);
                // remove it from the list and let the process die
                int index = mToastQueue.indexOf(record);
                if (index >= 0) {
                //移除Toast
                    mToastQueue.remove(index);
                }
                //唤醒进程
                keepProcessAliveIfNeededLocked(record.pid);
                if (mToastQueue.size() > 0) {
                //再次获取
                    record = mToastQueue.get(0);
                } else {
                    record = null;
                }
            }
        }
    }
```
最后如果是Toast为队列头，那么此时就会执行`showNextToastLocked()`方法，可以看到这里首先尝试获取队列头的Toast，后面居然是一个`while`循环，这块我感觉Google有点过度严谨了，可以看到如果没有取到`ToastRecord`,这里就移除后，再次执行唤醒进程，然后再次尝试获取，直到获取到，但是这样为了一个Toast的展示，甚至可能导致这个循环一直再执行，感觉有些不值当了，这只是我个人的看法，欢迎大家讨论。
当取到`ToastRecord`后，会执行其`callback`的`show`方法，当看到这个方法名的时候，感觉很熟悉，那么这个`callback`是什么对象呢，看一下`ToastRecord`的构造的地方。
```
public void enqueueToast(String pkg, ITransientNotification callback, int duration)
        {       
                        record = new ToastRecord(callingPid, pkg, callback, duration, token);
 
            }
        }
```
还是刚才那个函数，可看到，callback就是入参的对象，那么再看一下`Toast`的`show()`方法
```
public void show() {
        if (mNextView == null) {
            throw new RuntimeException("setView must have been called");
        }

        INotificationManager service = getService();
        String pkg = mContext.getOpPackageName();
        TN tn = mTN;
        tn.mNextView = mNextView;

        try {
            service.enqueueToast(pkg, tn, mDuration);
        } catch (RemoteException e) {
            // Empty
        }
    }
```
这样整个流程就通了，这个`callback`就是最初的`TN`对象，还是利用Binder的双向通信，所以这里就会回到`TN`对象的`show()`方法，这里要注意，再调用`show`方法的时候，会把刚才创建的`Token`对象，传入。
```
@Override
        public void show(IBinder windowToken) {
            if (localLOGV) Log.v(TAG, "SHOW: " + this);
            mHandler.obtainMessage(SHOW, windowToken).sendToTarget();
        }
```
这里有回到了最早分析的Handler对象，这个Handler对象常规使用的话是在主线程创建的。
```
mHandler = new Handler(looper, null) {
                @Override
                public void handleMessage(Message msg) {
                    switch (msg.what) {
                        case SHOW: {
                            IBinder token = (IBinder) msg.obj;
                            handleShow(token);
                            break;
                        }
                        case HIDE: {
                            handleHide();
                            // Don't do this in handleHide() because it is also invoked by
                            // handleShow()
                            mNextView = null;
                            break;
                        }
                        case CANCEL: {
                            handleHide();
                            // Don't do this in handleHide() because it is also invoked by
                            // handleShow()
                            mNextView = null;
                            try {
                                getService().cancelToast(mPackageName, TN.this);
                            } catch (RemoteException e) {
                            }
                            break;
                        }
                    }
                }
            };
```
可以看到又调用了`handleShow`方法。
```
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
                Context context = mView.getContext().getApplicationContext();
                String packageName = mView.getContext().getOpPackageName();
                if (context == null) {
                    context = mView.getContext();
                }
                mWM = (WindowManager)context.getSystemService(Context.WINDOW_SERVICE);
                // We can resolve the Gravity here by using the Locale for getting
                // the layout direction
                final Configuration config = mView.getContext().getResources().getConfiguration();
                final int gravity = Gravity.getAbsoluteGravity(mGravity, config.getLayoutDirection());
                mParams.gravity = gravity;
                if ((gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.FILL_HORIZONTAL) {
                    mParams.horizontalWeight = 1.0f;
                }
                if ((gravity & Gravity.VERTICAL_GRAVITY_MASK) == Gravity.FILL_VERTICAL) {
                    mParams.verticalWeight = 1.0f;
                }
                mParams.x = mX;
                mParams.y = mY;
                mParams.verticalMargin = mVerticalMargin;
                mParams.horizontalMargin = mHorizontalMargin;
                mParams.packageName = packageName;
                mParams.hideTimeoutMilliseconds = mDuration ==
                    Toast.LENGTH_LONG ? LONG_DURATION_TIMEOUT : SHORT_DURATION_TIMEOUT;
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
这里的代码就比较简单了，将基础的属性设置到了LayoutParams，这里比较重要的是将token设置到了`LayoutParams`中(关于这个属性后面可能会有一篇博客专门讲解一下这个属性值和权限的关系，本篇博客主要分析Toast的展示原理，就不拓展分析了)，并且利用`WindowManager`的`addView`的上，这样最终`Toast`就显示出来了。
剩下了就是怎么移除这个Toast了，回到NMS，再`show`后，使用`scheduleDurationReachedLocked(record);`方法，就是移除操作。
```
private void scheduleDurationReachedLocked(ToastRecord r)
    {
        mHandler.removeCallbacksAndMessages(r);
        Message m = Message.obtain(mHandler, MESSAGE_DURATION_REACHED, r);
        //显示耗时只有两种
        long delay = r.duration == Toast.LENGTH_LONG ? LONG_DELAY : SHORT_DELAY;
        //通过Handler发送消息执行
        mHandler.sendMessageDelayed(m, delay);
    }
```
这里第一个注意的点，可以看到，这里`delay`变量只有两种可能，`LONG_DELAY `和`SHORT_DELAY `。这也就解释了为什么我们平时使用`Toast`组件，不支持自定义显示时长，只能有`LONG`和`SHORT`两种时长。
然后通过Handler发送一个延时消息，用于隐藏Toast组件。
```
@Override
        public void handleMessage(Message msg)
        {
            switch (msg.what)
            {
                case MESSAGE_DURATION_REACHED:
                    handleDurationReached((ToastRecord)msg.obj);
                    break;
               ...
            }
        }
        
private void handleDurationReached(ToastRecord record)
    {
        if (DBG) Slog.d(TAG, "Timeout pkg=" + record.pkg + " callback=" + record.callback);
        synchronized (mToastQueue) {
        //定位消息位置
            int index = indexOfToastLocked(record.pkg, record.callback);
            if (index >= 0) {
            //取消消息
                cancelToastLocked(index);
            }
        }
    }
```
这里的逻辑很简单，就是利用Handler的消息机制，取出显示的消息的位置，然后进行取消操作。
```
@GuardedBy("mToastQueue")
    void cancelToastLocked(int index) {
    		//取出消息
        ToastRecord record = mToastQueue.get(index);
        try {
        //执行隐藏逻辑
            record.callback.hide();
        } catch (RemoteException e) {
            Slog.w(TAG, "Object died trying to hide notification " + record.callback
                    + " in package " + record.pkg);
            // don't worry about this, we're about to remove it from
            // the list anyway
        }
        //移除操作
        ToastRecord lastToast = mToastQueue.remove(index);

        mWindowManagerInternal.removeWindowToken(lastToast.token, false /* removeWindows */,
                DEFAULT_DISPLAY);
        // We passed 'false' for 'removeWindows' so that the client has time to stop
        // rendering (as hide above is a one-way message), otherwise we could crash
        // a client which was actively using a surface made from the token. However
        // we need to schedule a timeout to make sure the token is eventually killed
        // one way or another.
        scheduleKillTokenTimeout(lastToast.token);

        keepProcessAliveIfNeededLocked(record.pid);
        if (mToastQueue.size() > 0) {
            // Show the next one. If the callback fails, this will remove
            // it from the list, so don't assume that the list hasn't changed
            // after this point.
            //显示下一个
            showNextToastLocked();
        }
    }
```
知道了`show`的逻辑后，这个的原理就很相似了，这里首先取出`ToastRecord`变量，其实我感觉这里Google可以优化一下，刚才先是定位，然后这里又取出，相当于两次遍历，其实可以合并为一次遍历就可以。
* 然后利用Binder执行`hide`方法。
* 将给Toast 生成的窗口Token从WMS 服务中删除
* 判断是否还有消息，如果存在，则继续显示Toast
这里再看一下`hide`方法。同样也是利用Handler,最终执行`handleHide()`方法。
```
public void handleHide() {
            if (localLOGV) Log.v(TAG, "HANDLE HIDE: " + this + " mView=" + mView);
            if (mView != null) {
                // note: checking parent() just to make sure the view has
                // been added...  i have seen cases where we get here when
                // the view isn't yet added, so let's try not to crash.
                if (mView.getParent() != null) {
                    if (localLOGV) Log.v(TAG, "REMOVE! " + mView + " in " + this);
                    mWM.removeViewImmediate(mView);
                }


                // Now that we've removed the view it's safe for the server to release
                // the resources.
                try {
                    getService().finishToken(mPackageName, this);
                } catch (RemoteException e) {
                }

                mView = null;
            }
        }
```
这里还是利用WMS将View移除，这里有个地方挺有意思，这里先判断了一下view的`parent`不为null,这里的注释写的很口语化,Google的工程师也挺有意思。
```
// note: checking parent() just to make sure the view has
// been added...  i have seen cases where we get here when
// the view isn't yet added, so let's try not to crash.
```
至此，整个流程就分析完毕了。
### 总结
这里来回顾总结一下`Toast`的展示原理
>1. 首先通过构建Toast对象，内部创建了`TN`对象，这个对象是一个Binder对象。
>2. `show`方法的实质是调用NMS的代理，执行`enqueueToast`方法，并且传入`TN`对象用于双向通信。
>3. NMS中，将Toast的显示构建成了一个`ToastRecord`对象，并且有一个队列用于保存。
>4. NMS将`ToastRecord`加入队列后，最终利用`TN`对象，执行`show`方法
>5. TN对象的`show`方法，最后是利用`Handler`发送消息，最后执行添加，就是利用WindowManager将Toast的View加入Window。
>6. NMS中执行完后，内部也会利用Handler发送延时消息，只有两种`LONG`和`SHORT`，消息收到后，同样也是通过`TN`对象，执行`hide`方法
>7. 同样的流程，TN利用Handler发送消息，最终执行，同样利用WindowManager，移除View。
>8. NMS执行完移除操作后，会判断队列中是否还有消息，如果有继续执行展示Toast的逻辑。

本篇博客主要是针对`Toast`组件的展示原理进行讲解，后面有时间会继续分析Toast相关的问题，和Window相关的问题。
