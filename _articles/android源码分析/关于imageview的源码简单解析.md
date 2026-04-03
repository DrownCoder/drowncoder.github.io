---
title: "关于ImageView的源码简单解析"
category: "Android源码分析"
category_slug: "android源码分析"
source_name: "关于ImageView的源码简单解析"
sort_key: 0064
---
今天在设置ImageView的图片时无意遇到一些问题，区分了一下设置background和src的区别，顺便看了一下View的setBackgroundDrawable源码(ImageView继承View调用的是View的方法)。将理解的简单总结一下，以便下一次接着看~
源码：
```
    /**
     * @deprecated use {@link #setBackground(Drawable)} instead
     */
    @Deprecated
    public void setBackgroundDrawable(Drawable background) {
        computeOpaqueFlags();
/*background为null，直接return*/
        if (background == mBackground) {
            return;
        }
/*requestLayout初始化为false，用于最后requestLayout()方法对requestLayout变量进行判断，如果为true，就调用requestLayout()方法。

requestLayout()：当view确定自身已经不再适合现有的区域时，该view本身调用这个方法要求parent view重新调用他的onMeasure onLayout来对重新设置自己位置。*/
        boolean requestLayout = false;

        mBackgroundResource = 0;
/*下面这一小段代码是用来判断，当view中已有内容时，清除已有内容的相关属性。其中调用unscheduleDrawable()方法在后面有介绍，主要是用来解除原有内容的相关事件，这块我也没有理解太清楚，只能理解为这样。。。*/
        /*
         * Regardless of whether we're setting a new background or not, we want
         * to clear the previous drawable.
         */
        if (mBackground != null) {
            mBackground.setCallback(null);
            unscheduleDrawable(mBackground);
        }
/*sThreadLocal系统临时创建的矩形，用于未来扩展*/
        if (background != null) {
            Rect padding = sThreadLocal.get();
            if (padding == null) {
                padding = new Rect();
                sThreadLocal.set(padding);
            }
            resetResolvedDrawables();
           /*设置图片是从左到右还是从右到左对齐，依据父组件*/ background.setLayoutDirection(getLayoutDirection());
            if (background.getPadding(padding)) {
                resetResolvedPadding();
                switch (background.getLayoutDirection()) {
                    case LAYOUT_DIRECTION_RTL:
                        mUserPaddingLeftInitial = padding.right;
                        mUserPaddingRightInitial = padding.left;
                        internalSetPadding(padding.right, padding.top, padding.left, padding.bottom);
                        break;
                    case LAYOUT_DIRECTION_LTR:
                    default:
                        mUserPaddingLeftInitial = padding.left;
                        mUserPaddingRightInitial = padding.right;
                        internalSetPadding(padding.left, padding.top, padding.right, padding.bottom);
                }
                mLeftPaddingDefined = false;
                mRightPaddingDefined = false;
            }
/*当原本没用内容，或者原本的内容的最小大小和新的内容的最小大小不相同时，设置 requestLayout为true，调用 requestLayout()方法*/
            // Compare the minimum sizes of the old Drawable and the new.  If there isn't an old or
            // if it has a different minimum size, we should layout again
            if (mBackground == null || mBackground.getMinimumHeight() != background.getMinimumHeight() ||
                    mBackground.getMinimumWidth() != background.getMinimumWidth()) {
                requestLayout = true;
            }

            background.setCallback(this);
            if (background.isStateful()) {
                background.setState(getDrawableState());
            }
            background.setVisible(getVisibility() == VISIBLE, false);
            mBackground = background;

            if ((mPrivateFlags & PFLAG_SKIP_DRAW) != 0) {
                mPrivateFlags &= ~PFLAG_SKIP_DRAW;
                mPrivateFlags |= PFLAG_ONLY_DRAWS_BACKGROUND;
                requestLayout = true;
            }
        } else {//新的内容为空时
            /* Remove the background */
            mBackground = null;

            if ((mPrivateFlags & PFLAG_ONLY_DRAWS_BACKGROUND) != 0) {
                /*
                 * This view ONLY drew the background before and we're removing
                 * the background, so now it won't draw anything
                 * (hence we SKIP_DRAW)
                 */
                mPrivateFlags &= ~PFLAG_ONLY_DRAWS_BACKGROUND;
                mPrivateFlags |= PFLAG_SKIP_DRAW;
            }

            /*
             * When the background is set, we try to apply its padding to this
             * View. When the background is removed, we don't touch this View's
             * padding. This is noted in the Javadocs. Hence, we don't need to
             * requestLayout(), the invalidate() below is sufficient.
             */

            // The old background's minimum size could have affected this
            // View's layout, so let's requestLayout
            requestLayout = true;
        }

        computeOpaqueFlags();
// requestLayout()方法
        if (requestLayout) {
            requestLayout();
        }

        mBackgroundSizeChanged = true;
        invalidate(true);
    }
```

以上只是为了以后学习记录，如有错误希望指出，感谢~
