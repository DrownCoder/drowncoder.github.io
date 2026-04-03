继续入自定义View的坑，最近实现一个效果的时候，需要动态添加和删除View，所以就要用到ViewGroup中的removeView和addView，按理来说应该很简单，但是我遇到了一个问题，发现removeView无效。  
**最后发现：当你要remove的View正在执行Animation效果的时候，是无法remove掉的，所以需要先clearAnimation，再remove**

从源码中证实了我的观点：

```
    public void removeViewAt(int index) {
        removeViewInternal(index, getChildAt(index));
        requestLayout();
        invalidate(true);
    }
```

我调用的是removeViewAt方法，可以看到，实际上起作用的是removeViewInternal方法

```
private void removeViewInternal(int index, View view) {
        ...

        if (view.getAnimation() != null || (mTransitioningViews != null 
                        &&mTransitioningViews.contains(view))) {
            addDisappearingView(view);
        } else if (view.mAttachInfo != null) {
           view.dispatchDetachedFromWindow();
        }	
        ...
    }
```

一样，当我第一样看到这个方法，我是拒绝的，很长的方法体，非常多的变量不知道含义，第一次看我没有找到原因。第二次再看的时候，我发现了上面这段代码，非常符合我要寻找的问题，**当View的Animation不是null的时候，会执行addDisappearingView(view)**

```
    /**
     * Add a view which is removed from mChildren but still needs animation
     *
     * @param v View to add
     */
    private void addDisappearingView(View v) {
        ArrayList<View> disappearingChildren = mDisappearingChildren;

        if (disappearingChildren == null) {
            disappearingChildren = mDisappearingChildren = new ArrayList<View>();
        }

        disappearingChildren.add(v);
    }
```

可以看到，Google的解释其实已经很清楚了，添加一个带有动画效果的View。
**我看到这还是有点不确定，这里面没有真正意义上的将Remove的View重绘到组件上。**
所以我查询了mDisappearingChildren这个对象，看在哪里使用了这个对象

```
@Override
    protected void dispatchDraw(Canvas canvas) {
        ...

        // Draw any disappearing views that have animations
        if (mDisappearingChildren != null) {
            final ArrayList<View> disappearingChildren = mDisappearingChildren;
            final int disappearingCount = disappearingChildren.size() - 1;
            // Go backwards -- we may delete as animations finish
            for (int i = disappearingCount; i >= 0; i--) {
                final View child = disappearingChildren.get(i);
                more |= drawChild(canvas, child, drawingTime);
            }
        }
        ...
    }
```

可以看到，我在dispatchDraw方法中找到了我想要的结果，可以看到，注释写的也很清楚，**在重绘的时候，会将仍然有Animation的View绘制出来。**
可以看到，这里遍历了mDisappearingChildren，调用了drawChild进行绘制。

到此问题解决，小小的看了一下源码，也是很有趣的                                                      
