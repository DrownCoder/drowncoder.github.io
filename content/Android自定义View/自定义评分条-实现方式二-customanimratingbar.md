---
title: "自定义评分条（实现方式二）-CustomAnimRatingBar"
date: 2017-09-26 00:30:07+08:00
categories: ["Android自定义View"]
source_name: "自定义评分条（实现方式二）-CustomAnimRatingBar"
jianshu_views: 573
jianshu_url: "https://www.jianshu.com/p/b24ea83e9798"
---
接着上一篇博客[http://blog.csdn.net/sdfdzx/article/details/75447981](http://blog.csdn.net/sdfdzx/article/details/75447981 "CustomRatingBar"),由于需求变动，需要星星在滑动的时候能够有动画效果，由于CustomRatingBar是基于自定义View，实现onDraw绘制而成，实现动画效果比较困难，所以只能考虑从用另一个方式实现这个组件，这篇博文就是用ViewGroup实现自定义评分条并且实现动画效果。

#### 功能特性![效果](/assets/img/posts/d16ec735ea493c70.webp)
1.可设置星星大小  
2.可设置星星之间的间距  
3.可以设置星星图片（填充图片和半填充图片）  
4.可以设置星星是否可触摸评分  
5.可设置评分范围（整颗 | 半颗 ）  **此处不支持随意**
6.可以设置总星量

#### 实现思路
1.利用自定义ViewGroup继承LinearLayout,动态添加ImageView实现。
2.根据进度动态设置ImageView的图片背景。
3.重写onTouchEvent,利用属性动画在MOVE事件时实现动画效果。

#### 实现难点
1.触摸进度的判断。
2.属性动画的实现。
3.一定的滑动冲突处理。

#### 整体代码

```
package com.study.dzx.library.widget;

import android.animation.ObjectAnimator;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.drawable.Drawable;
import android.support.annotation.Nullable;
import android.util.AttributeSet;
import android.view.Gravity;
import android.view.MotionEvent;
import android.widget.ImageView;
import android.widget.LinearLayout;

import com.study.dzx.library.R;
import com.study.dzx.library.utils.DensityUtils;


/**
 * Author : Xuan.
 * Data : 2017/7/12.
 * Description :
 * 星星评分-viewgroup
 * -可动画
 */

public class CustomAnimRatingBar extends LinearLayout {
    //星星个数
    private int mStarNum;
    //星星之间的距离
    private int mStarDistance;
    //星星的大小
    private int mStarSize;
    //空星星图片
    private Drawable mEmptyStar;
    //填充的星星的照片
    private Drawable mFillStar;
    //半个星星的图片
    private Drawable mHalfStar;
    //星星的进度
    private float mTouchStarMark;
    //上次的星星进度
    private float mLastMark;
    //是否显示半个
    private boolean mShowHalf;
    //显示星星的个数
    private int mShowNum;
    //触摸模式 1--单个星星 2--半个星星
    private int mMode;
    //是否可以触摸
    private boolean mTouchAble;

    private int mLastX;
    private int mLastY;

    //星星变化接口
    public interface onStarChangedListener {
        void onStarChange(CustomAnimRatingBar ratingBar, float mark);
    }

    private onStarChangedListener mOnStarChangeListener;

    public void setmOnStarChangeListener(onStarChangedListener mOnStarChangeListener) {
        this.mOnStarChangeListener = mOnStarChangeListener;
    }

    private Context mContext;

    public CustomAnimRatingBar(Context context) {
        this(context, null);
    }

    public CustomAnimRatingBar(Context context, @Nullable AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public CustomAnimRatingBar(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        setOrientation(HORIZONTAL);
        initAttr(context, attrs);
        initView();
    }

    /**
     * 和ScrollView嵌套时滑动冲突
     */
    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        int x = (int) ev.getX();
        int y = (int) ev.getY();
        switch (ev.getAction()) {
            case MotionEvent.ACTION_DOWN:{
                getParent().requestDisallowInterceptTouchEvent(true);
                break;
            }
            case MotionEvent.ACTION_MOVE:{
                int deltaX = x - mLastX;
                int deltaY = y - mLastY;
                if (Math.abs(deltaX) > Math.abs(deltaY)) {
                    getParent().requestDisallowInterceptTouchEvent(true);
                }else {
                    getParent().requestDisallowInterceptTouchEvent(false);
                }
            }

        }
        mLastX = x;
        mLastY = y;
        return super.dispatchTouchEvent(ev);
    }
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (!mTouchAble) {
            return super.onTouchEvent(event);
        }
        float x = event.getX();
        float touchStar = x / getWidth() * mStarNum;
        if (touchStar <= 0.5f) {
            touchStar = 0.5f;
        }
        if (touchStar > mStarNum) {
            touchStar = mStarNum;
        }

        switch (mMode) {
            case 1://整个星星
            {
                touchStar = (float) Math.ceil(touchStar);
                break;
            }
            case 2://half
            {
                if ((touchStar - Math.floor(touchStar) <= 0.5)&& touchStar - Math.floor(touchStar)!=0) {
                    touchStar = (float) (Math.floor(touchStar) + 0.5f);
                } else {
                    touchStar = (float) Math.ceil(touchStar);
                }
                break;
            }
        }

        mShowHalf = false;
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN: {
                setRating(touchStar);
                ObjectAnimator
                        .ofFloat(getChildAt(mShowNum - 1), "translationY", 0, -20, 0)
                        .setDuration(300).start();
                break;
            }
            case MotionEvent.ACTION_MOVE: {
                setRating(touchStar);
                if (mTouchStarMark != mLastMark) {
                    ObjectAnimator
                            .ofFloat(getChildAt(mShowNum - 1), "translationY", 0, -20, 0)
                            .setDuration(300).start();
                }
                mLastMark = mTouchStarMark;
                break;
            }
            case MotionEvent.ACTION_UP: {
                break;
            }

        }
        return true;
    }

    private void fillStar() {
        mShowNum = (int) Math.ceil(mTouchStarMark);
        if ((mTouchStarMark - Math.floor(mTouchStarMark)) <= 0.5f &&
                mTouchStarMark - Math.floor(mTouchStarMark) != 0) {
            mShowNum = (int) Math.ceil(mTouchStarMark);
            mShowHalf = true;
        }
        for (int i = 0; i < mShowNum - 1; i++) {
            ((ImageView) getChildAt(i)).setImageDrawable(mFillStar);
        }
        if (mShowHalf) {
            ((ImageView) getChildAt(mShowNum - 1)).setImageDrawable(mHalfStar);
        } else {
            ((ImageView) getChildAt(mShowNum - 1)).setImageDrawable(mFillStar);
        }

        resetView();
    }

    /**
     * 设置评分
     */
    public void setRating(float touchStar) {

        if (mOnStarChangeListener != null) {
            this.mOnStarChangeListener.onStarChange(this, touchStar);
        }
        mTouchStarMark = touchStar;
        fillStar();
    }

    /**
     * 获得评分
     */
    public float getRating() {
        return mTouchStarMark;
    }

    /**
     * 设置是否可以点击
     */
    public void setTouchAble(boolean mTouchAble) {
        this.mTouchAble = mTouchAble;
    }

    /**
     * 重置空白星星
     */
    private void resetView() {
        for (int i = mStarNum - 1; i > mShowNum - 1; i--) {
            ((ImageView) getChildAt(i)).setImageDrawable(mEmptyStar);
        }
    }

    private void initView() {
        for (int i = 0; i < mStarNum; i++) {
            ImageView iv = new ImageView(mContext);
            LayoutParams layoutParams = new LayoutParams(mStarSize
                    , mStarSize);
            layoutParams.gravity = Gravity.CENTER_VERTICAL;
            layoutParams.setMargins(mStarDistance / 2, 0, mStarDistance / 2, 0);
            iv.setLayoutParams(layoutParams);
            iv.setImageDrawable(mEmptyStar);
            this.addView(iv);
        }
    }

    private void initAttr(Context context, AttributeSet attrs) {
        TypedArray array = context.obtainStyledAttributes(attrs, R.styleable.CustomAnimRatingBar);
        mStarNum = array.getInteger(R.styleable.CustomAnimRatingBar_starAnimNum, 5);
        mStarDistance = array.getDimensionPixelSize(R.styleable.CustomAnimRatingBar_starAnimDistance, DensityUtils.dp2px(context, 0));
        mStarSize = array.getDimensionPixelSize(R.styleable.CustomAnimRatingBar_starAnimSize, DensityUtils.dp2px(context, 20));
        mEmptyStar = array.getDrawable(R.styleable.CustomAnimRatingBar_starAnimEmpty);
        mFillStar = array.getDrawable(R.styleable.CustomAnimRatingBar_starAnimFill);
        mHalfStar = array.getDrawable(R.styleable.CustomAnimRatingBar_starAnimHalf);
        mMode = array.getInt(R.styleable.CustomAnimRatingBar_modeAnim, 2);
        mTouchAble = array.getBoolean(R.styleable.CustomAnimRatingBar_touchAbleAnim, true);
        mTouchStarMark = array.getInt(R.styleable.CustomAnimRatingBar_ratingAnimProgress, 0);
        array.recycle();
        this.mContext = context;
        if (mMode == 1) {
            mHalfStar = mFillStar;
        }
    }
}

```

#### 关键代码
##### 1.initView方法
    private void initView() {
        for (int i = 0; i < mStarNum; i++) {
            ImageView iv = new ImageView(mContext);
            LayoutParams layoutParams = new LayoutParams(mStarSize
                    , mStarSize);
            layoutParams.gravity = Gravity.CENTER_VERTICAL;
            layoutParams.setMargins(mStarDistance / 2, 0, mStarDistance / 2, 0);
            iv.setLayoutParams(layoutParams);
            iv.setImageDrawable(mEmptyStar);
            this.addView(iv);
        }
    }
根据对应的星星数量，动态添加ImageView作为为灰的星星，并且利用LayoutParams来设置星星的大小和星星之间的间距。
##### 2.onTouchEvent()
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (!mTouchAble) {
            return super.onTouchEvent(event);
        }
        float x = event.getX();
        float touchStar = x / getWidth() * mStarNum;
        if (touchStar <= 0.5f) {
            touchStar = 0.5f;
        }
        if (touchStar > mStarNum) {
            touchStar = mStarNum;
        }

        switch (mMode) {
            case 1://整个星星
            {
                touchStar = (float) Math.ceil(touchStar);
                break;
            }
            case 2://half
            {
                if ((touchStar - Math.floor(touchStar) <= 0.5)&& touchStar - Math.floor(touchStar)!=0) {
                    touchStar = (float) (Math.floor(touchStar) + 0.5f);
                } else {
                    touchStar = (float) Math.ceil(touchStar);
                }
                break;
            }
        }

        mShowHalf = false;
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN: {
                setRating(touchStar);
                ObjectAnimator
                        .ofFloat(getChildAt(mShowNum - 1), "translationY", 0, -20, 0)
                        .setDuration(300).start();
                break;
            }
            case MotionEvent.ACTION_MOVE: {
                setRating(touchStar);
                if (mTouchStarMark != mLastMark) {
                    ObjectAnimator
                            .ofFloat(getChildAt(mShowNum - 1), "translationY", 0, -20, 0)
                            .setDuration(300).start();
                }
                mLastMark = mTouchStarMark;
                break;
            }
            case MotionEvent.ACTION_UP: {
                break;
            }

        }
        return true;
    }
1)首先得到触摸的坐标，利用触摸的坐标x/组件的长度 * 星星的总个数得到需要的星星进度。
 

```
float touchStar = x / getWidth() * mStarNum;
```

2)区分整个星星还是半颗星星
  

```
  switch (mMode) {
            case 1://整个星星
            {
                touchStar = (float) Math.ceil(touchStar);
                break;
            }
            case 2://half
            {
                if ((touchStar - Math.floor(touchStar) <= 0.5)&& touchStar - Math.floor(touchStar)!=0) {
                    touchStar = (float) (Math.floor(touchStar) + 0.5f);
                } else {
                    touchStar = (float) Math.ceil(touchStar);
                }
                break;
            }
        }
```

如果是整颗星星模式，则将进度直接向上取整。
如果是半颗星星，对于小数位大于0.5的就向上取整，对于小数位小于0.5的就将整数位向下取整，再加0.5的进度。

3）

```
switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN: {
                setRating(touchStar);
                ObjectAnimator
                        .ofFloat(getChildAt(mShowNum - 1), "translationY", 0, -20, 0)
                        .setDuration(300).start();
                break;
            }
            case MotionEvent.ACTION_MOVE: {
                setRating(touchStar);
                if (mTouchStarMark != mLastMark) {
                    ObjectAnimator
                            .ofFloat(getChildAt(mShowNum - 1), "translationY", 0, -20, 0)
                            .setDuration(300).start();
                }
                mLastMark = mTouchStarMark;
                break;
            }
            case MotionEvent.ACTION_UP: {
                break;
            }

        }
```

首先看setRating方法
   

```
 /**
     * 设置评分
     */
    public void setRating(float touchStar) {

        if (mOnStarChangeListener != null) {
            this.mOnStarChangeListener.onStarChange(this, touchStar);
        }
        mTouchStarMark = touchStar;
        fillStar();
    }
```

这里面进行接口回调，并且进行星星图片的填充。对应fillStar()方法
   

```
 private void fillStar() {
        mShowNum = (int) Math.ceil(mTouchStarMark);
        if ((mTouchStarMark - Math.floor(mTouchStarMark)) <= 0.5f &&
                mTouchStarMark - Math.floor(mTouchStarMark) != 0) {
            mShowNum = (int) Math.ceil(mTouchStarMark);
            mShowHalf = true;
        }
        for (int i = 0; i < mShowNum - 1; i++) {
            ((ImageView) getChildAt(i)).setImageDrawable(mFillStar);
        }
        if (mShowHalf) {
            ((ImageView) getChildAt(mShowNum - 1)).setImageDrawable(mHalfStar);
        } else {
            ((ImageView) getChildAt(mShowNum - 1)).setImageDrawable(mFillStar);
        }

        resetView();
    }
```

这里的处理方法同CustomRatingBar，例如一个进度是3.5，则先填充3，最后填充0.5个星星。如果是4，则先填充3，最后填充1个星星。
  

```
  /**
     * 重置空白星星
     */
    private void resetView() {
        for (int i = mStarNum - 1; i > mShowNum - 1; i--) {
            ((ImageView) getChildAt(i)).setImageDrawable(mEmptyStar);
        }
    }
```

resetView则将剩余的空白星星制空。
 

```
   ObjectAnimator
                        .ofFloat(getChildAt(mShowNum - 1), "translationY", 0, -20, 0)
                        .setDuration(300).start();
```

setRating方法执行完，则执行动画效果，这里利用属性动画里面的translationY，进行跳动效果，具体的动画效果也可以在此处进行相应的修改。

```
    /**
     * 和ScrollView嵌套时滑动冲突
     */
    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        int x = (int) ev.getX();
        int y = (int) ev.getY();
        switch (ev.getAction()) {
            case MotionEvent.ACTION_DOWN:{
                getParent().requestDisallowInterceptTouchEvent(true);
                break;
            }
            case MotionEvent.ACTION_MOVE:{
                int deltaX = x - mLastX;
                int deltaY = y - mLastY;
                if (Math.abs(deltaX) > Math.abs(deltaY)) {
                    getParent().requestDisallowInterceptTouchEvent(true);
                }else {
                    getParent().requestDisallowInterceptTouchEvent(false);
                }
            }

        }
        mLastX = x;
        mLastY = y;
        return super.dispatchTouchEvent(ev);
    }
```

这里涉及到一个滑动冲突问题，就是当该组件和ScrollView嵌套时，向下的ScrollView滑动和横向的星星滑动，当歇着滑动的时候，就会出现星星的滑动被ScrollView消费，导致无法触动星星的滑动。所以为了解决这个问题，就需要处理滑动冲突。
可以看到这里重写了dispathTouchEvent（）,利用requestDisallowInterceptTouchEvent（true）进行拦截。这里的处理逻辑就是，当DOWN事件时进行拦截，交给星星处理，当是MOVE事件时，对滑动的X和Y轴的方向的距离进行判断，如果X>Y，则进行拦截，如果Y>X，则交给ScrollView处理。

#### 总结
这里大体的实现思路分析完了，总的来说没有特别的难点，主要就是处理自定义组件的细节问题需要多注意，多在细节进行优化。这里提供Github地址[https://github.com/sdfdzx/CustomRatingBar/blob/master/library/src/main/java/com/study/dzx/library/widget/CustomAnimRatingBar.java](https://github.com/sdfdzx/CustomRatingBar/blob/master/library/src/main/java/com/study/dzx/library/widget/CustomAnimRatingBar.java "CustomAnimRatingBar")
