---
title: "自定义评分条（实现方式一）-CustomRatingBar"
date: 2017-09-26 00:28:40+08:00
categories: ["Android自定义View"]
source_name: "自定义评分条（实现方式一）-CustomRatingBar"
jianshu_views: 895
jianshu_url: "https://www.jianshu.com/p/ebbbf3e95f2e"
---
Android原生的RatingBar是一个评分组件，但是局限性比较多，像星星大小不好调整，星星之间的间距不好调整,不可以小数制的评分等，为了应对需求，开发出一个可自定义性较强的评分组件。
#### 功能特性
1.可设置星星大小  
2.可设置星星之间的间距  
3.可以设置星星图片（填充图片和未填充图片）  
4.可以设置星星是否可触摸评分  
5.可设置评分范围（整颗 | 半颗 | 随意）  
6.可以设置总星量

![一颗](http://upload-images.jianshu.io/upload_images/7866586-ec0a8a47e9be322b?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)---------![半颗](http://upload-images.jianshu.io/upload_images/7866586-f81f4b2372599851?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
![随意](http://upload-images.jianshu.io/upload_images/7866586-f18656aaef03f4ae?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

#### 实现思路
1.绘制背景灰色星星  
2.在背景上根据评分大小绘制亮的星星  
3.重写onTouchEvent事件，根据手的触摸范围重绘完成触摸

#### 实现难点
1.重写onMeasure,通过星星个数计算组件大小  
2.根据手的触摸位置绘制星星，利用将drawable转换成Bitmap后，利用canvas.translate和canvas.drawRect函数绘制。
3.根据不同的模式，判断触摸位置对应的星星进度。

#### 关键代码
##### 1.onMeasure方法

```
@Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        int widthSize = MeasureSpec.getSize(widthMeasureSpec);
        int widthMode = MeasureSpec.getMode(widthMeasureSpec);
        int heightSize = MeasureSpec.getSize(heightMeasureSpec);
        int heightMode = MeasureSpec.getMode(heightMeasureSpec);

        int width;
        int height;
        if (widthMode == MeasureSpec.EXACTLY) {
            width = widthSize;
        } else {
            width = getPaddingLeft() + mStarNum * mStarSize
                    + (mStarNum - 1) * mStarDistance + getPaddingRight();
        }
        if (heightMode == MeasureSpec.EXACTLY) {
            height = heightSize;
        } else {
            height = getPaddingTop() + mStarSize + getPaddingBottom();
        }

        setMeasuredDimension(width, height);
    }
```

    

既然这个自定义View是拿canvas和paint进行绘制，所以需要重写onMeasure方法，主要是针对wrap_content进行测量。
1.EXACTLY
当是绝对长度是，height=heightSize,width = widthSize;
2.其他情况（wrap_content->AT_MOST，另一种UNSPECIFIED一般不考虑）
width=左内距+一颗星星的大小*星星的个数+（星星的个数-1）*星星与星星之间的间距+右内距
heith=上内距+一颗星星的大小+下内距

###### 2.onDraw方法
    
    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (mEmptyStar == null) {
            return;
        }
        for (int i = 0; i < mStarNum; i++) {
            mEmptyStar.setBounds(i * (mStarSize + mStarDistance), 0
                    , mStarSize + i * (mStarSize + mStarDistance), mStarSize);
            mEmptyStar.draw(canvas);
        }

        if (mTouchStarMark < 1) {
            canvas.drawRect(0, 0, mStarSize * mTouchStarMark, mStarSize, mPaint);
        } else {
            canvas.drawRect(0, 0, mStarSize, mStarSize, mPaint);

            for (int i = 1; i <= mTouchStarMark - 1; i++) {
                canvas.translate(mStarDistance + mStarSize, 0);
                canvas.drawRect(0, 0, mStarSize, mStarSize, mPaint);
            }
            float lastMark = mTouchStarMark - (int) mTouchStarMark;
            canvas.translate((mStarDistance + mStarSize), 0);
            canvas.drawRect(0, 0, mStarSize * lastMark, mStarSize, mPaint);
        }
    }
    
下面假设星星个数为5个
绘制过程分为两步：1.绘制5个灰色的星星作为背景；2.根据评分的进度绘制相应进度的亮星星。
（1）绘制5个灰色的星星
    
	for (int i = 0; i < mStarNum; i++) {
            mEmptyStar.setBounds(i * (mStarSize + mStarDistance), 0
                    , mStarSize + i * (mStarSize + mStarDistance), mStarSize);
            mEmptyStar.draw(canvas);
        }
    

可以看到还是非常简单的，根据需要绘制的星星个数循环，setBounds的四个参数分别表示绘制Drawable的地方。
第一个星星：left=0*(星星的大小+星星的间距)=0；top=0;right=一个星星的大小+0*（星星的大小+星星的间距）=星星的大小；bottom=星星的大小；
第二个星星：left=星星的大小+星星的间距；top=0；right=两颗星星的大小+星星的间距；bottom:星星的大小；
理解起来可以看这个图：*-*-*-*-*

（2）根据进度绘制相应的亮星星。
**这里有个地方需要注意，由于drawable.draw只能绘制一整个drawable，而这里需要考虑三种模式：整颗|半颗|随意，所以就不能用上面一种方式进行绘制，这里需要将drawable装换为bitmap，然后利用canvas.translate进行移动，利用canvas.drawRect绘制一定范围的不完整的星星**

	if (mTouchStarMark < 1) {
            canvas.drawRect(0, 0, mStarSize * mTouchStarMark, mStarSize, mPaint);
        } else {
            canvas.drawRect(0, 0, mStarSize, mStarSize, mPaint);

            for (int i = 1; i <= mTouchStarMark - 1; i++) {
                canvas.translate(mStarDistance + mStarSize, 0);
                canvas.drawRect(0, 0, mStarSize, mStarSize, mPaint);
            }
            float lastMark = mTouchStarMark - (int) mTouchStarMark;
            canvas.translate((mStarDistance + mStarSize), 0);
            canvas.drawRect(0, 0, mStarSize * lastMark, mStarSize, mPaint);
        }

（1）这里先考虑当mTouchStarMark(进度)<1的情况，由于不能走循环，所以直接绘制canvas.drawRect(left,top,right,bottom，paint)
left = 0 ; top = 0; right = 星星的大小*进度；bottom：星星的大小
（2）后面将mTouchStarMark分为两种可能，mTouchStarMark=1.5,mTouchStarMark=4.5;
根据后面的for循环条件可以看出，1.5-1=0.5是无法循环的，既然这里mTouchStarMark>=1，所以先绘制一个星星。
    canvas.drawRect(0, 0, mStarSize, mStarSize, mPaint);
也就是可以理解为4.5=1+3+0.5，这种绘制方式，先绘制一个，再绘制中间的整数个，最后绘制尾数的小数位。
这里要注意canvas.translate位移是叠加的，所以for循环中每次只需要位移（一个星星+星星间距）的距离，然后绘制一个星星
    canvas.translate(mStarDistance + mStarSize, 0);
                canvas.drawRect(0, 0, mStarSize, mStarSize, mPaint);
最后通过float-int获得小数位，同样再位移一次，绘制小数位的星星
    float lastMark = mTouchStarMark - (int) mTouchStarMark;
            canvas.translate((mStarDistance + mStarSize), 0);
            canvas.drawRect(0, 0, mStarSize * lastMark, mStarSize, mPaint);

###### onTouchEvent
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (!mTouchAble) {
            return super.onTouchEvent(event);
        }
        float x = event.getX();
        if (x == 0 || x > (mStarNum * (mStarSize + mStarDistance) - mStarDistance)) {
            return true;
        } else {
            int n = (int) (x / (mStarDistance + mStarSize));
            float touchStar = n + (x - n * (mStarDistance + mStarSize)) / mStarSize;
            switch (mMode) {
                case 1://整个星星
                    touchStar = (float) Math.ceil(touchStar);
                    break;
                case 2://随意
                    break;
                case 3: {
                    //半个
                    if ((touchStar - Math.floor(touchStar) <= 0.5)) {
                        touchStar = (float) (Math.floor(touchStar) + 0.5f);
                    } else {
                        touchStar = (float) Math.ceil(touchStar);
                    }
                    break;
                }
            }
            /**
             * 触摸后最小值为0.5
             */
            if (touchStar <= 0.5f) {
                touchStar = 0.5f;
            }
            switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN: {
                    setRating(touchStar);
                    break;
                }
                case MotionEvent.ACTION_MOVE: {
                    setRating(touchStar);
                    break;
                }
                case MotionEvent.ACTION_UP:
                    break;
            }
        }
        invalidate();

        return true;
    }

重写onTouchEvent这里主要需要在方法体中根据触摸的坐标和对应的展示模式得到对应的星星进度。
    int n = (int) (x / (mStarDistance + mStarSize));
            float touchStar = n + (x - n * (mStarDistance + mStarSize)) / mStarSize;
首先根据触摸的坐标x/一个星星所占的长度（星星间距+星星大小），再强转为int的得到填充满的星星个数。
假设触摸到4.5的位置，则n=4,touchStar = 4+0.5 = 4.5。
 

```
 switch (mMode) {
                case 1://整个星星
                    touchStar = (float) Math.ceil(touchStar);
                    break;
                case 2://随意
                    break;
                case 3: {
                    //半个
                    if ((touchStar - Math.floor(touchStar) <= 0.5)) {
                        touchStar = (float) (Math.floor(touchStar) + 0.5f);
                    } else {
                        touchStar = (float) Math.ceil(touchStar);
                    }
                    break;
                }
            }
```

接下来根据触摸模式对触摸进度进行相应的改变。
整个：4.5就向上转型= 5
随意：break
半个的话：1)小数位<0.5则将进度补为0.5；2）小数位>0.5则将进度为补为向上取整。

    switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN: {
                    setRating(touchStar);
                    break;
                }
                case MotionEvent.ACTION_MOVE: {
                    setRating(touchStar);
                    break;
                }
                case MotionEvent.ACTION_UP:
                    break;
            }
接下来根据触摸事件，每次都调用setRating方法。

```
 /**
     * 设置评分
     */
    public void setRating(float touchStar) {
        if (mOnStarChangeListener != null) {
            this.mOnStarChangeListener.onStarChange(this, touchStar);
        }
        mTouchStarMark = touchStar;
        invalidate();
    }
```

在setRating方法中执行接口回调，再**重绘**

#### 总结
这个是以自定义View的形式自定义RatingBar，后面会再写一篇以自定义ViewGroup的方式展示自定义RatingBar。

这个项目的源代码[https://github.com/sdfdzx/CustomRatingBar](https://github.com/sdfdzx/CustomRatingBar "GitHub/CustomRatingBar")
