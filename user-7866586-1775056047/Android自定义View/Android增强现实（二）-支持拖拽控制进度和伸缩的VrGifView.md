>1.[Android增强现实（一）-AR的三种方式(展示篇)](https://www.jianshu.com/p/e6a51f4439df)
>2.[Android增强现实（二）-支持拖拽控制进度和伸缩的VrGifView](https://www.jianshu.com/p/abd1772cb061)
>3.[Android增强现实（三）-3D模型展示器](https://www.jianshu.com/p/f1708d5277ad)
### 前言
前段时间研究了一下增强现实在Android端的实现，目前大体分为两种，全景立体图（GIF和全景图）和3D模型图。这篇博客主要讲一下关于GIF相关的实现方式。
###  效果
![VrGifView](http://upload-images.jianshu.io/upload_images/7866586-ef7c6eb4e2392371.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

### 使用方式	
1.Add it in your root build.gradle at the end of repositories:

	allprojects {
		repositories {
			...
			maven { url 'https://jitpack.io' }
		}
	}
Step 2. Add the dependency

	dependencies {
	       compile 'com.github.sdfdzx:VRShow:v1.0.2'
	}

 XML and Java
```
<com.study.xuan.gifshow.widget.VrGifView
        android:id="@+id/gif"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:src="@drawable/demo"
        />


public class GifActivity extends AppCompatActivity {
    private VrGifView mGif;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_gif);
        mGif = (VrGifView) findViewById(R.id.gif);
        mGif.setTouch(true);//是否 可触摸
        mGif.setDrag(true);//是否可拖拽
        mGif.setScale(false);//是否可伸缩
        mGif.setMoveMode(VrGifView.MODE_FAST);//触摸响应速度
    }
}
```
### 技术分析
![京东 ](http://upload-images.jianshu.io/upload_images/7866586-3e60f0d9040c9e28.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

大家应该在淘宝和京东上看到过这样的实现效果吧，我对他的分析是这样的：
>1.首先这是一个商品全景自动旋转的gif图。
>2.这个gif图支持进度的调整。（淘宝支持拖拽控制，京东支持陀螺仪传感器控制）

基于以上的分析首先我们要实现的组件肯定要支持这几个关键点：
1.支持播放gif
2.支持gif的进度控制（**重要**）

这两个条件其实就第一个来说Glide就可以实现，但是第二个条件就比较难了，其实gif就是图片集的播放，想控制gif的进度，目前Glide我还没有找到相关的api可以控制（大家知道的话可以评论告诉我~），考虑到第二个条件，我最后选用了比较知名的Android端加载Gif的开源库[android-gif-drawable](https://github.com/koral--/android-gif-drawable "android-gif-drawable")，这个库提供了对应的api来对进度进行控制。
```
Animation control
GifDrawable implements an Animatable and MediaPlayerControl so you can use its methods and more:

stop() - stops the animation, can be called from any thread
start() - starts the animation, can be called from any thread
isRunning() - returns whether animation is currently running or not
reset() - rewinds the animation, does not restart stopped one
setSpeed(float factor) - sets new animation speed factor, eg. passing 2.0f will double the animation speed
seekTo(int position) - seeks animation (within current loop) to given position (in milliseconds)
getDuration() - returns duration of one loop of the animation
getCurrentPosition() - returns elapsed time from the beginning of a current loop of animation
```

目前两个前提条件找到了，现在的问题就是手势控制进度了，目前看起来一帆风顺没有什么坑，继续往下实现。
### 功能
既然前提条件已经具备，现在就来提需求：
>1.支持单指拖动
>2.支持双指缩放
>3.考虑一定的性能
### 实现关键点
**一.单指拖动**
单指拖动似乎很简单
**实现思路：**
1.获取滑动的距离
2.获取Gif的总进度，和MOVE时的当前的进度
3.滑动距离/屏幕宽度 = MOVE时的当前的进度/Gif的总进度，对应将滑动距离转换成GIF的进度，从而通过seekTo来控制GIF的进度。

**关键代码：**
```
private void rotateModel(MotionEvent event) {
        switch (event.getAction() & MotionEvent.ACTION_MASK) {
            case MotionEvent.ACTION_DOWN:
                if (touchMode == TOUCH_NONE && event.getPointerCount() == 1) {
                    touchMode = TOUCH_DRAG;
                    gifDrawable.stop();
                    lastX = event.getX();
                    downTime = event.getDownTime();
                }
                break;
            case MotionEvent.ACTION_MOVE:
                if (touchMode == TOUCH_DRAG) {
					//通过move的时间控制刷新频率
                    if ((event.getEventTime() - downTime) > moveSpeed) {
                        moveX = event.getX();
                        moveDis = moveX - lastX;
                        lastX = moveX;
                        curPos = gifDrawable.getCurrentPosition();
                        if ((curPos + moveDis * PX_TO_POS) < 0) {
                            curPos += moveDis * PX_TO_POS + gifLength;
                        } else {
                            curPos += moveDis * PX_TO_POS;
                        }
                        if (curPos < 0) {
                            curPos = 0;
                        }
                        gifDrawable.seekTo(curPos);
                        downTime = event.getEventTime();
                    }
                }
                break;
            case MotionEvent.ACTION_UP:
                if (touchMode == TOUCH_DRAG) {
                    touchMode = TOUCH_NONE;
                }
                gifDrawable.start();
                break;
        }
    }
```

思路滤清了，代码还是很好理解的，这里唯一需要注意的地方：**注意对于界面刷新频率的控制，一开始我没有考虑这一点，简单的只是移动了就改变进度，这时会发现在MOVE的过程中，gif会不停的闪黑屏，一开始我以为是我计算进度有问题，怎么改都没有解决，后来我看了下GifDrawable的源码，每次都会重绘，我就怀疑是由于MOVE过程中的滑动触发频率过快，导致刷新过快导致的，我便通过MOVE的时间来控制**
```
if ((event.getEventTime() - downTime) > moveSpeed)
```
可以看到这里通过move时的时间点和down的时间点相减来控制触发刷新的频率，这里的moveSpeed是可以调整的。
```
/**
     * 设置触摸触发响应速度
     */
    public void setMoveMode(int mode) {
        switch (mode) {
            case MODE_FAST:
                moveMode = MODE_FAST;
                moveSpeed = SPEED_FAST;
                break;
            case MODE_NORMAL:
                moveMode = MODE_NORMAL;
                moveSpeed = SPEED_NORMAL;
                break;
            case MODE_LOW:
                moveMode = MODE_LOW;
                moveSpeed = SPEED_LOW;
                break;
            default:
                moveMode = MODE_NORMAL;
                moveSpeed = SPEED_NORMAL;
                break;
        }
    }
```

**二.双指缩放**
网上对于双指缩放的做法很多，有通过矩阵变换，有通过canvas的，这里我考虑到原图是一个GIF，对于双指缩放，我选择使用属性动画来实现。
**实现思路：**
1.获得双指的距离
2.将距离转换为scale的缩放量
3.利用ObjectAnimator来实现缩放。

**关键代码：**
```
private void zoomScale(MotionEvent event) {
        switch (event.getAction() & MotionEvent.ACTION_MASK) {
            // starts pinch
            case MotionEvent.ACTION_POINTER_DOWN:
                if (event.getPointerCount() >= 2) {
                    pinchStartDistance = getPinchDistance(event);
                    downTime = event.getDownTime();
                    if (pinchStartDistance > 50f) {
                        touchMode = TOUCH_ZOOM;
                    }
                }
                break;

            case MotionEvent.ACTION_MOVE:
                if (touchMode == TOUCH_ZOOM && pinchStartDistance > 0) {
                    // on pinch
                    if ((event.getEventTime() - downTime) > moveSpeed) {
                        if (getPinchDistance(event) > pinchStartDistance) {
                            //递增
                            isUp = true;
                        } else {
                            isUp = false;
                        }
                        pinchScale = getPinchDistance(event) / pinchStartDistance;
                        if (checkScale(pinchScale)) {
                            changeScale(pinchScale);
                        }
                    }
                }
                break;

            // end pinch
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_POINTER_UP:
                pinchScale = 0;
                if (touchMode == TOUCH_ZOOM) {
                    touchMode = TOUCH_NONE;
                }
                break;
        }
    }
```

这里转化其实和上面的原理相近，但是这里有同样有几个坑需要踩一下：
**难点：**
1.刷新频率
2.手指缩放误差

和上面一样，当我一气呵成实现后发现并没有想象的那么简单，实现效果会发现当我双指放大的时候，GIF的大小总是有时候会莫名其妙的变小，我通过将缩放量LOG打出来发现，虽然我们的双指手势是放大，但是在放大的过程中由于停顿等其他原因会有间歇性的变小的趋势，这样GIF就会出现在变大的过程中变小，为了避免这样的出现，我的解决思路是这样的：

>1.过滤超小范围的起始点
>2.通过移动趋势判断时变大还是变小
>3.执行动画之前判断要执行的动画是否符合当前的变化趋势。

```
case MotionEvent.ACTION_POINTER_DOWN:
                if (event.getPointerCount() >= 2) {
                    pinchStartDistance = getPinchDistance(event);
                    downTime = event.getDownTime();
					//过滤超小范围的起始点
                    if (pinchStartDistance > 50f) {
                        touchMode = TOUCH_ZOOM;
                    }
                }
                break;
```
可以看到我在down的时候对于超小范围的起始点是进行了过滤的，只有大于50的才算双指缩放。

```
case MotionEvent.ACTION_MOVE:
                if (touchMode == TOUCH_ZOOM && pinchStartDistance > 0) {
                    // on pinch
                    if ((event.getEventTime() - downTime) > moveSpeed) {
						//判断趋势
                        if (getPinchDistance(event) > pinchStartDistance) {
                            //递增
                            isUp = true;
                        } else {
                            isUp = false;
                        }
                        pinchScale = getPinchDistance(event) / pinchStartDistance;
						//检查变化是否符合趋势
                        if (checkScale(pinchScale)) {
                            changeScale(pinchScale);
                        }
                    }
                }
                break;


private boolean checkScale(float pinchScale) {
        if (canAnim) {
            if (isUp) {
                if (pinchScale > 1) {
                    return true;
                }
            } else {
                if (pinchScale < 1) {
                    return true;
                }
            }
        }
        return false;
    }
```
可以看到，这里比较了和down的时候的距离变化，来判断时变大还是变小，最后在执行动画前先判断一下当前执行的动画是否符合我们的移动趋势，符合才执行动画，不符合不执行。


### 总结

具体难点已经分析完毕了，主要就是多思考一下，其实也没有特别复杂的地方，只是在巨人的肩膀上封装了一下，这里放上源码地址
>github地址：[VRShow](https://github.com/sdfdzx/VRShow "VRShow")
>喜欢的点个Star，谢谢~

