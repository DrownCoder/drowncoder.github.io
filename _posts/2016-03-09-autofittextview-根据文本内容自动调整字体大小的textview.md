---
title: "AutoFitTextView-根据文本内容自动调整字体大小的TextView"
date: 2016-03-09 08:00:00 +0800
categories: ["Android自定义View"]
source_name: "AutoFitTextView-根据文本内容自动调整字体大小的TextView"
---
![效果](http://upload-images.jianshu.io/upload_images/7866586-e3af0017c5ca3ef2?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
上次完成的[仿网易新闻标签选择器（可拖动）-TabMoveLayout](http://blog.csdn.net/sdfdzx/article/details/70230959)有个问题，那就是因为标签的宽度是固定的，当标签文字过长的时候，就会显示不全，网易新闻的处理方法是缩小字体使得标签可以包容下文字。所以就对应将这种方式实现了出来。
#### 实现思路：
因为宽度是固定的，而TextView的实现方式其实是通过Paint绘制的，所以我们可以通过width=paint.measureText()和TextView的实际宽度比较，当循环width<=实际宽度的时候的字号则是合适的字号，不合适则将字号-1。

所以代码还是很简单的：

```
package com.study.library;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.support.annotation.Nullable;
import android.support.v7.widget.AppCompatTextView;
import android.util.AttributeSet;
import android.util.Log;
import android.util.TypedValue;

/**
 * Created by Xuan on 2017/4/18.
 */

public class AutoFitTextView extends AppCompatTextView {
    private float mDefaultTextSize;
    private Paint mTextPaint;
    public AutoFitTextView(Context context) {
        this(context ,null);
    }

    private void initAttr() {
        mTextPaint = new Paint();
        mTextPaint.set(getPaint());
        mDefaultTextSize = getTextSize();
    }

    public AutoFitTextView(Context context, @Nullable AttributeSet attrs) {
        this(context, attrs , 0);
    }

    public AutoFitTextView(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        initAttr();
    }

    @Override
    protected void onTextChanged(CharSequence text, int start, int lengthBefore, int lengthAfter) {
        super.onTextChanged(text, start, lengthBefore, lengthAfter);
        refitText(text.toString(),getWidth());
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        refitText(getText().toString(),getWidth());
    }

    public void refitText(String text, int textWidth){
        Log.e("refit", "refit:"+text+"width:"+textWidth);
        if(textWidth > 0){
            int availableTextWidth = textWidth - getPaddingLeft() - getPaddingRight();
            float tsTextSize = mDefaultTextSize;
            mTextPaint.setTextSize(tsTextSize);
            float length = mTextPaint.measureText(text);
            while (length > availableTextWidth) {
                tsTextSize--;
                mTextPaint.setTextSize(tsTextSize);
                length = mTextPaint.measureText(text);
            }
            setTextSize(TypedValue.COMPLEX_UNIT_PX,tsTextSize);
            invalidate();
        }
    }
    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
    }
}
```
