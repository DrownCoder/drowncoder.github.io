---
title: "竖向Viewpager原理实现（3D卡片翻动效果画廊）"
date: 2017-09-26 00:29:50+08:00
categories: ["Android自定义View"]
source_name: "竖向Viewpager原理实现（3D卡片翻动效果画廊）"
jianshu_views: 2590
jianshu_url: "https://www.jianshu.com/p/ee8a37ea736d"
---
![效果](http://upload-images.jianshu.io/upload_images/7866586-0c1cab5626ed883b?imageMogr2/auto-orient/strip)
### 效果：
1.竖向的Viewpager
2.3D翻动效果
3.Glide加载图片

### 实现思路：
1.Viewpager的竖向滑动：可以参照[stackoverflow](http://stackoverflow.com/questions/13477820/android-vertical-viewpager)中的一篇帖子，这里面有很多种方式。
这里说下我的实现方式：**交换触摸位置的x,y方向，利用PageTransformer的transformPage()方法，在移动过程中通过translation动态改变页面方向实现竖向移动。**
2.3D翻转效果：也是利用PageTransformer的transformPage()方法，主要通过setRotationX方法，绕X轴旋转，这里**注意要改变视角距离**不然无法实现效果。

### 主要代码：
	/**
     * Swaps the X and Y coordinates of your touch event.
     */
    private MotionEvent swapXY(MotionEvent ev) {
        float width = getWidth();
        float height = getHeight();

        float newX = (ev.getY() / height) * width;
        float newY = (ev.getX() / width) * height;

        ev.setLocation(newX, newY);

        return ev;
    }

    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {
        boolean intercepted = super.onInterceptTouchEvent(swapXY(ev));
        return intercepted;
    }

可以看到这里，重写了onInterceptTouchEvent，在这里调用了swapXY方法，这个方法主要是交换了触摸位置的X,Y坐标，但是代码可能理解起来有点困难，可以这样理解：  
![](http://upload-images.jianshu.io/upload_images/7866586-40ba354207f4c4a1?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
Viewpager的默认布局方式如图所示，**也就是只能触发你的横向事件，竖向的滑动并不会影响Viewpager的滑动**。
这里为了使竖向的滑动起效果，可以看到newX = (ev.getY() / height) * width这里当你Y轴移动了，通过高宽比，转变成X轴的移动。  
当手指移动距离：ev.getY() = height,newX = height/height*width = width对应的X轴就移动了width长度，这也就为后来的实现提供了基础
当手指移动距离：ev.getX() = width,newY = width/width*height = height（这个其实对后面并没有影响，因为Viewpager不会触发Y轴的移动）

	private class VerticalPageTransformer implements ViewPager.PageTransformer {

        @Override
        public void transformPage(View view, float position) {
            if (position <= 0) {
                view.setAlpha(1);
                view.setTranslationY((float) (-view.getHeight() * (1 - Math.pow(0.9f, -position))));
                //设置缩放中点
                view.setPivotX(view.getWidth() / 2f);
                view.setPivotY(view.getHeight() / 2f);
                //设置缩放的比例 此处设置两个相邻的卡片的缩放比率为0.9f
                float Scale = (float) Math.pow(0.9f, -position);
                if (Scale > 0.7f) {
                    view.setScaleX(Scale);
                    view.setScaleY(Scale);
                } else {
                    view.setAlpha(0);
                }
            } else {//(0,++)
                view.setPivotY(view.getHeight());
                setCameraDistance(view);
                view.setRotationX(180 * -position);
                view.setAlpha(1 - position);
            }
            view.setTranslationX(view.getWidth() * -position);

        }
    }

重写的PageTransformer的transformPage的方法，这里重点要理解position参数。这里我画了个图方便理解，由图可见：
![](http://upload-images.jianshu.io/upload_images/7866586-062fdb6634a5a692?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)  
![](http://upload-images.jianshu.io/upload_images/7866586-0412b0f77aa62857?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
![](http://upload-images.jianshu.io/upload_images/7866586-9862d9497ae8ec01?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
初始时，前三张的position分别为0,1,2。  
向左滑动一页：前三张的position分别为-1,0,1
再向左滑一页：前三张的position分别为-2,-1,0
所以可以得到position的变化范围，当前页显示的position为0，当前页左边的显示的<0，当前页右边的显示的>0。
**这里我将当前页设置为最后一页（总量为8）**，那么显示的position分别为-7，-6...-2,-1,0
#### 现在来一步一步实现
**1.实现X坐标相同**
![](http://upload-images.jianshu.io/upload_images/7866586-d0eccd1dcce92cc8?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

```
view.setTranslationX(view.getWidth() * -position);
```

现在要将布局显示成竖向排列，所以很容易想到把每个View的X坐标+width*-position

这时候可以想到，所有的页面都重叠在一起，位置在position=0的地方。
**2.实现Y坐标逐减**
![](http://upload-images.jianshu.io/upload_images/7866586-cc61ee2432047aac?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)![](http://upload-images.jianshu.io/upload_images/7866586-96d601509b99db58?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
现在则需要将页面的Y坐标，分别向上移动一点距离，这里我通过0.9的幂函数来实现错开。

```
view.setTranslationY((float) (-view.getHeight() * (1 - Math.pow(0.9f, -position))));
```

position=0：对应的y
position=-1：要上移一点，y-height*(1-0.9) = y-height*0.1
position=-2：再上移一点，y-height*(1-0.9*0.9) = y-height*0.19
...以此类推
**3.实现逐层缩小**
这块应该就比较好实现了，现在position=0,-1,-2,-3,...,-7(我是设第一页显示末页，倒着来)

```
//设置缩放中点
                view.setPivotX(view.getWidth() / 2f);
                view.setPivotY(view.getHeight() / 2f);
                //设置缩放的比例 此处设置两个相邻的卡片的缩放比率为0.9f
                float Scale = (float) Math.pow(0.9f, -position);
                view.setScaleX(Scale);
                view.setScaleY(Scale);
```

可以看到，代码还是比较好理解的，前两句设置缩放中点，后面就是设置缩放比例为0.9的幂函数
position=0:对应Scale = 1
position=-1:Scale=0.9
position=-2:Scale=0.9*0.9=0.81
**4.实现3D绕轴旋转**

```
view.setPivotY(view.getHeight());
setCameraDistance(view);
                view.setRotationX(180 * -position);
    /**
     * 改变视角距离, 贴近屏幕
     */
    private void setCameraDistance(View view) {
        int distance = 10000;
        float scale = getResources().getDisplayMetrics().density * distance;
        view.setCameraDistance(scale);
    }
```

首先根据我们要实现的效果，可以发现我们是绕图片的下边线旋转的，所以我们首先设**轴为y=height**

```
view.setPivotY(view.getHeight());
```

setCameraDistance()这个函数我们等会说
这里我们轴确定了好就要确定我们的旋转的角度，根据效果，我们发现，我们旋转的角度是[0,-180]，而position的变化范围是[0,1]，所以代码就很好理解了

```
view.setRotationX(180 * -position);
```

一开始我以为这样就实现了效果，但是运行效果会发现很奇怪
![](http://upload-images.jianshu.io/upload_images/7866586-1f466c65474f59a2?imageMogr2/auto-orient/strip)
最后通过网上搜寻发现原因就是需要使用这个函数，改变视角距离，贴近屏幕，看起来才正确。

```
/**
     * 改变视角距离, 贴近屏幕
     */
    private void setCameraDistance(View view) {
        int distance = 10000;
        float scale = getResources().getDisplayMetrics().density * distance;
        view.setCameraDistance(scale);
    }
```

**5.透明度变化**
这块就很好理解了，我将position分为了两个区段，（负无穷，0），[0,正无穷)
(负无穷，0) alpha =1
[0,1] alpha =1-position逐渐透明
[1,正无穷）alpha <=0透明
**6.设置显示页数**
这里可以发现，实现出来的效果，后面的页会一直显示在后面，看起来密集恐惧症+强迫症有木有

```
 if (Scale > 0.7f) {
                    view.setScaleX(Scale);
                    view.setScaleY(Scale);
                } else {
                    view.setAlpha(0);
                }
```

所以我在这设置了一下，当缩放值小于0.7时，就让它隐藏。

关键点的实现大概已经分析了，这里给出[【GlideStudy】](https://github.com/sdfdzx/GlideStudy)链接，具体可以去看一看，欢迎*star*。
