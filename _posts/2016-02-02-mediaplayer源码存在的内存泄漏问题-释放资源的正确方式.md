---
title: "MediaPlayer源码存在的内存泄漏问题，释放资源的正确方式"
date: 2017-09-26 00:30:36+08:00
categories: ["Android源码分析"]
source_name: "MediaPlayer源码存在的内存泄漏问题，释放资源的正确方式"
jianshu_views: 6856
jianshu_url: "https://www.jianshu.com/p/77a0bd4690bd"
---
最近完成了一个联网的视频播放器Demo，闲来无聊，尝试了一下LeakCanary，一款Android查看内存泄漏的工具。使用方式

> https://www.liaohuqiu.net/cn/posts/leak-canary-read-me/
这个是LeakCanary的中文使用文档，很简单。

无意间发现应用存在内存泄漏问题。
LeakCanary提供的Log信息：

```
 D/LeakCanary: In com.shuyu.video.clean.debug:2.0.0:30305.
  * com.shuyu.video.activity.PlayActivity has leaked:
  * GC ROOT static com.shuyu.video.MyApplication.mApplication
  * references com.shuyu.video.MyApplication.mLoadedApk
  * references android.app.LoadedApk.mReceivers
  * references android.util.ArrayMap.mArray
  * references array java.lang.Object[].[3]
  * references android.util.ArrayMap.mArray
  * references array java.lang.Object[].[2]
  * references android.media.MediaPlayer$ProxyReceiver.this$0
  * references android.media.MediaPlayer.mProxyContext
  * leaks com.shuyu.video.activity.PlayActivity instance
                                                                         
```

可以看到，这个工具很强大很方便，直接指出了内存泄漏的地方，上面写的很清楚，倒数第二行说明了Mediaplayer存在一个代理引用，导致了PlayActivity无法回收，造成内存泄漏。

按理说，既然工具已经这么详细的说明了内存泄漏出现问题的地方，问题应该很好解决，但是，我查看了我的代码，mediaplayer容易出现内存泄漏的地方无非就是在和Activity进行生命周期的时候，需要自己进行释放资源，不然会造成内存泄漏。
附上我的关键代码吧：

```
    @Override
    protected void onDestroy() {
        super.onDestroy();
        ReleasePlayer();

    }

    /**
     * 释放播放器资源
     */
    private void ReleasePlayer() {
        if (player != null) {
            player.stop();
            player.release();
            player = null;
        }

    }
```

可以看到我重写了Activity的生命周期，在OnDestroy方法中释放了Mediaplayer的资源，释放Mediaplayer的资源的方法也是网络上常用的释放Meidplayer的步骤。但是问题来了，这样怎么会造成内存泄漏哪？

最后，还是老外厉害啊，在stackoverflow上找到一篇文章，问题一模一样，[原文链接](http://stackoverflow.com/questions/33221516/android-media-player-keeps-app-instance-and-cause-a-memory-leak)
![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-6bdc51c7c3caf7b4?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

大概意思是，他查看了Mediaplayer的源码，发现存在一个引用，应该回收，但是在release方法中，并没有没处理，只有在reset方法中，这个引用才被消除。
**所以结论来了：**释放资源的正确方式：

```
    /**
     * 释放播放器资源
     */
    private void ReleasePlayer() {
        if (player != null) {
            player.stop();
            
            //关键语句
            player.reset();
            
            player.release();
            player = null;
        }

    }
```

具体到源码，是哪一个没有回收，大概看了一下
**Mediaplayer的release源码：**

```
    public void release() {
        baseRelease();
        stayAwake(false);
        updateSurfaceScreenOn();
        mOnPreparedListener = null;
        mOnBufferingUpdateListener = null;
        mOnCompletionListener = null;
        mOnSeekCompleteListener = null;
        mOnErrorListener = null;
        mOnInfoListener = null;
        mOnVideoSizeChangedListener = null;
        mOnTimedTextListener = null;
        if (mTimeProvider != null) {
            mTimeProvider.close();
            mTimeProvider = null;
        }
        mOnSubtitleDataListener = null;
        _release();
    }
```

reset的源码：

```
public void reset() {
        mSelectedSubtitleTrackIndex = -1;
        synchronized(mOpenSubtitleSources) {
            for (final InputStream is: mOpenSubtitleSources) {
                try {
                    is.close();
                } catch (IOException e) {
                }
            }
            mOpenSubtitleSources.clear();
        }
        if (mSubtitleController != null) {
            mSubtitleController.reset();
        }
        if (mTimeProvider != null) {
            mTimeProvider.close();
            mTimeProvider = null;
        }

        stayAwake(false);
        _reset();
        // make sure none of the listeners get called anymore
        if (mEventHandler != null) {
            mEventHandler.removeCallbacksAndMessages(null);
        }

        synchronized (mIndexTrackPairs) {
            mIndexTrackPairs.clear();
            mInbandTrackIndices.clear();
        };
    }
```

我查了reset中的对象，发现mSubtitleController 这个对象在release方法中没有被处理，只在reset方法中被reset了，并且mSubtitleController 的构造方法会存在context对象，我猜应该就是这个对象，导致内存泄漏这个问题存在吧

```
mSubtitleController = new SubtitleController(context, mTimeProvider, MediaPlayer.this);
```

**问题的正确与否，具体源码原理和原因待求大神解释。**
