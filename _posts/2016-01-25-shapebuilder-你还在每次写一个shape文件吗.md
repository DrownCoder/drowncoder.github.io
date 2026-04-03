---
title: "ShapeBuilder-你还在每次写一个Shape文件吗？"
date: 2018-01-29 21:39:02+08:00
categories: ["Android开源项目"]
source_name: "ShapeBuilder-你还在每次写一个Shape文件吗？"
jianshu_views: 2007
jianshu_url: "https://www.jianshu.com/p/040290e4b448"
---
不知道大家有没有过这样的烦恼，打开Drawable文件夹下到处都是各式各样的shape定义，其中不乏有一模一样的样式，但只是名字不同，或者仅仅只是radius，color不同，但每次一有边框，圆角，点击效果等都需要定义一个新的shape，今天这个页面圆角要2dp，明天一样的又要4dp，或是颜色的变化都需要我们重新写一个shape.xml,至少我每次写的时候都有点受不了，为了避免每次这样做重复的定义，这里为大家分享一个我用java代码来控制shape的生成，动态改变shape的样式。
![效果](http://upload-images.jianshu.io/upload_images/7866586-d449de5373a38c55.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
### 源码地址
[SupperShape](https://github.com/sdfdzx/SupperShape)

### 主要特性
* 不用再写shape.xml文件了！！！
* 链式调用
* 涵盖Shape几乎常用的所有属性，如：TYPE，Radius，Stroke，Soild，Gradient，GradientType，GradientCenter，GradientRadius，Size
* 支持Selector
* 支持Layer-list

### 如何使用
**1.ShapeBuilder**
非常简单，来看看最基本的使用方式，比如一个带边框的View。
```
ShapeBuilder.create()
            .Type(RECTANGLE)
            .Soild(Color.RED)
            .Stroke(5,Color.BLACK)
            .build(View);
```
>设置对应的属性，调用build(View)传入需要设置背景的view即可。如果需要获得构建的drawable可以调用该build()方法返回。

利用Builder模式，实现了一系列的链式调用，方便我们设置属性值。
```
public interface IShape {
    public ShapeBuilder Type(int type);

    public ShapeBuilder Stroke(int px, int color);

    public ShapeBuilder Stroke(int px, int color, int dashWidth, int dashGap);

    public ShapeBuilder Solid(int color);

    public ShapeBuilder Radius(float px);

    public ShapeBuilder Radius(float topleft, float topright, float botleft, float botright);

    public ShapeBuilder Gradient(int startColor, int centerColor, int endColor);

    public ShapeBuilder Gradient(int angle, int startColor, int centerColor, int endColor);

    public ShapeBuilder Gradient(GradientDrawable.Orientation orientation, int startColor, int
            centerColor, int endColor);

    public ShapeBuilder GradientType(int type);

    public ShapeBuilder GradientCenter(float x, float y);

    public ShapeBuilder GradientRadius(float radius);

    public ShapeBuilder setSize(int width, int height);

    public void build(View v);

    public GradientDrawable build();
}
```
**2.ShapeListBuilder替代Selector**
其实这个是基于ShapeBuilder，将几个主要的都顺便封装了一下，可以替代Selector的定义。
```
ShapeListBuilder.create(Drawable drawable)//传默认状态下的drawable
                .addShape(Drawable shape, int... state)//状态对应的drawable和state
                .build(View view);
```
![点击效果](http://upload-images.jianshu.io/upload_images/7866586-25c590a3443829cc.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

**3.LayerBuilder替代Layer-list**
用于替代Layer
```
LayerBuilder.create(Drawable... drawables)
			.Bottom(1, 15)//top，right...setInset等
			.build(View view);
```
用法其实都比较简单无脑，记住要最后调用build(View view)方法~

### 原理
原理其实也比较基础，我们每次定义Shape文件，其实最后会被生成GradientDrawable，通过查看GradientDrawable源码，我们其实能看到我们定义的type，Radius，solid等属性其实就是最后在这里面通过TypeArray读取出来，最后生成了GradientDrawable对象，所以我们只是需要对GradientDrawable源码进行阅读理解，考虑到GradientDrawable属性众多这一特点，利用Build模式进行封装，便实现了ShapeBuilder，当然内部还有一些对于低版本兼容的处理优化，大家可以阅读源码。而后两个原理也是一样的，分别对应StateListDrawable和LayerDrawable。

最后再次附上源码地址[SupperShape](https://github.com/sdfdzx/SupperShape "SupperShape")，大家要是使用过程中有什么不错的建议，欢迎提issue或者评论，顺手点个star那就更好不错了~

