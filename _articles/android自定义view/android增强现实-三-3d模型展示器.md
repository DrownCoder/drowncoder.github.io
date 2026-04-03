---
title: "Android增强现实（三）-3D模型展示器"
category: "Android自定义View"
category_slug: "android自定义view"
source_name: "Android增强现实（三）-3D模型展示器"
sort_key: 0067
---
>1.[Android增强现实（一）-AR的三种方式(展示篇)](https://www.jianshu.com/p/e6a51f4439df)
>2.[Android增强现实（二）-支持拖拽控制进度和伸缩的VrGifView](https://www.jianshu.com/p/abd1772cb061)
>3.[Android增强现实（三）-3D模型展示器](https://www.jianshu.com/p/f1708d5277ad)

### 前言
前段时间研究了一下增强现实在Android端的实现，目前大体分为两种，全景立体图（GIF和全景图）和3D模型图。这篇博客主要讲一下关于3D模型的展示方式吧。

![3D模型](http://upload-images.jianshu.io/upload_images/7866586-d5490c38cdcd32b1.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

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
<com.study.xuan.stlshow.widget.STLView
        android:id="@+id/stl"
        android:layout_width="match_parent"
        android:layout_height="match_parent"/>
```
java
```
//读取STL文件类
		STLViewBuilder
			.init(STLView stlView)
			.Reader(ISTLReader reader)
			.Byte(byte[] bytes)
			.File(File file)
			.Assets(Context context, String fileName)
			.InputStream(InputStream inputStream)
			.build();
//基础使用方法
        STLViewBuilder.init(mStl).Assets(this, "bai.stl").build();
        mStl.setTouch(true);//是否可以触摸
        mStl.setScale(true);//是否可以缩放
        mStl.setRotate(true);//是否可以拖拽
        mStl.setSensor(true);//是否支持陀螺仪
		//stl文件读取过程中的回调
		mStl.setOnReadCallBack(new OnReadCallBack() {
            @Override
            public void onStart() {}
            @Override
            public void onReading(int cur, int total) {}
            @Override
            public void onFinish() {}
        });
```
### 技术分析
对于3D模型的渲染其实对于平常的应用平台其实涉及的还是比较少的，在游戏平台应用广泛，我无意中在京东看到过这样的功能
![京东3D](http://upload-images.jianshu.io/upload_images/7866586-39948650ce4759f4.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

起先我平常对于这种效果接触的比较少，还不太清楚怎么实现，后来才了解到关于OpenGL的相关知识才了解到这种实现方式其实是利用OpenGL和GLSurfaceView进行实现。

大概了解了实现可行性，我们来看一下**需求：**
>1.支持渲染3D模型
>2.支持单指拖拽
>3.支持双指缩放
>4.支持陀螺仪
>5.支持读取时的异步回调

对于这个的实现方式首先要了解这几个**知识点：**
>1.3D模型，STL文件格式
>2.OpenGL相关知识
>3.GLSurfaceView的使用

### 3D模型，STL文件格式
其实对于3D模型的渲染，这里其实要明白的就是我们要做的就是两步：

1.3D模型数据文件->模型数据（异步读取文件过程）
2.模型数据->模型展示（渲染展示过程）

这里只涉及STL文件格式的3D模型数据，不同的文件格式，读取文件的格式也不一样，我目前就实现了STL文件格式的，那么问题来了，何为STL文件，为什么要了解STL文件？
我们其实没必要了解那么深入，这里引入百度百科的介绍其实已经够我们进行了解；
>STL是用三角网格来表现3D CAD模型的一种文件格式。

可能这样我们理解还是比较困难，那么再加一张图
![3D模型](http://upload-images.jianshu.io/upload_images/7866586-7a23f5760c9c8581.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

上图可以看到是一个由STL文件描述的猫，就是由一个个小的三角形构成的，所以说STL描述的就是构成这个3D模型所用的所有的三角形的相关数据。
那么我们就需要了解一下STL文件是怎么描述三角形数据的。
STL文件分为两种格式，一种是ASCII明码格式，另一种是二进制格式。
**ASCII明码格式：**（以下引自百度百科）
>ASCII码格式的STL文件逐行给出三角面片的几何信息，每一行以1个或2个关键字开头。
>在STL文件中的三角面片的信息单元 facet 是一个带矢量方向的三角面片，STL三维模型就是由一系列这样的三角面片构成。
>整个STL文件的首行给出了文件路径及文件名。
>在一个 STL文件中，每一个facet由7 行数据组成，
>facet normal 是三角面片指向实体外部的法矢量坐标，
>outer loop 说明随后的3行数据分别是三角面片的3个顶点坐标，3顶点沿指向实体外部的法矢量方向逆时针排列。
```
明码://字符段意义
solidfilenamestl//文件路径及文件名
facetnormalxyz//三角面片法向量的3个分量值
outerloop
vertexxyz//三角面片第一个顶点坐标
vertexxyz//三角面片第二个顶点坐标
vertexxyz//三角面片第三个顶点坐标
endloop
endfacet//完成一个三角面片定义
 
......//其他facet
 
endsolidfilenamestl//整个STL文件定义结束
```
看到上面的介绍,其实不难发现,其实对于ASCII码格式的STL文件我们需要怎么读取哪？其实很简单，有固定的字段表示文件的开始和结束，有固定的字段表示一个三角的开始和结束，固定每个三角形由7行数据构成，固定每一行表示的含义，这所有的都是固定的，一个for循环，按照文件的格式读取即可。
**二进制格式：**（以下引自百度百科）
>二进制STL文件用固定的字节数来给出三角面片的几何信息。
>文件起始的80个字节是文件头，用于存贮文件名；
>紧接着用 4 个字节的整数来描述模型的三角面片个数，
>后面逐个给出每个三角面片的几何信息。每个三角面片占用固定的50个字节，依次是:
>3个4字节浮点数(角面片的法矢量)
>3个4字节浮点数(1个顶点的坐标)
>3个4字节浮点数(2个顶点的坐标)
>3个4字节浮点数(3个顶点的坐标)个
>三角面片的最后2个字节用来描述三角面片的属性信息。
>一个完整二进制STL文件的大小为三角形面片数乘以 50再加上84个字节。
```
UINT8//Header//文件头
UINT32//Numberoftriangles//三角面片数量
//foreachtriangle（每个三角面片中）
REAL32[3]//Normalvector//法线矢量
REAL32[3]//Vertex1//顶点1坐标
REAL32[3]//Vertex2//顶点2坐标
REAL32[3]//Vertex3//顶点3坐标
UINT16//Attributebytecountend//文件属性统计
```
其实读取方法和上面的相似，只不过上面的是操作文件的行，这里就是操作字节数了，可以看到每个三角面占用的字节数固定，固定的字节数内数据依次占用固定的字节数，所以还是一个for循环，按照字节的格式读取即可。

### OpenGL相关知识
OpenGL的相关知识怎么说哪，很多渲染过程中的相关api我也没搞懂，这里只说几个我们实现过程中需要了解的吧（具体网上资料很多，这方面我反正是个小白，就不充胖子了）。
1.glTranslatef（x,y,z）
2.glRotatef（angle,x,y,z）
3.glScalef（x,y,z）
看到字面意思就很好理解吧，平移，旋转，缩放，有api就好说了，剩下的就是我们将我们触摸得到的量转化成这里面的数值就行。

### GLSurfaceView的使用
GLSurfaceView是Android一个专门处理3D模型的的View，他的基本用法和平常的View没什么差异，唯一需要注意的就是需要调用```setRenderer()```传入一个```Renderer```对象。理解起来也比较容易，GLSurfaceView其实就是一个View,也就是一个展示的视图，而控制展示的也就是```Renderer```对象了。Renderer其实是一个接口，对应有三个方法需要我们实现，onSurfaceCreated对应视图创建时调用，onSurfaceChanged对应视图改变时调用，onDrawFrame对应视图绘制时调用。
```
public interface Renderer {
        void onSurfaceCreated(GL10 gl, EGLConfig config);
        void onSurfaceChanged(GL10 gl, int width, int height);
        void onDrawFrame(GL10 gl);
    }
```
对应配合上面OpenGL的相关知识，其实大概的实现过程已经有个雏形了。

### 关键代码
1.读取STL文件（这里以ASCII格式为例）
这里我是定义了一个读取的接口ISTLReader
```

public interface ISTLReader {
    public STLModel parserBinStl(byte[] bytes);

    public STLModel parserAsciiStl(byte[] bytes);

    public void setCallBack(OnReadListener listener);
}
```
可以通过STLViewBuilder.Reader(ISTLReader reader)方法自己实现。
我默认实现的STLReader这里只放上对于ASCII格式文件读取的伪代码吧。
```
public STLModel parserAsciiStl(byte[] bytes) {
        ...
        String stlText = new String(bytes);
        String[] stlLines = stlText.split("\n");
        vertext_size = (stlLines.length - 2) / 7;
        ...
        for (int i = 0; i < stlLines.length; i++) {
            String string = stlLines[i].trim();
            if (string.startsWith("facet normal ")) {
                string = string.replaceFirst("facet normal ", "");
                String[] normalValue = string.split(" ");
                for (int n = 0; n < 3; n++) {
                    ...
                }
            }
            if (string.startsWith("vertex ")) {
                string = string.replaceFirst("vertex ", "");
                String[] vertexValue = string.split(" ");
                ...
            }

            ...
        }
      ...
    }
```
这里可以看到我是将byte[]转为了String，接着就通过固定的格式来进行读取，伪代码在上面，便于理解读取过程，可以看到，基本的就是通过对行数，startsWith，split等对字符串处理的函数进行读取的，读取规则其实可以仿照上面对于**STL文件格式**的介绍。
2.自定义Renderer渲染
自定义Renderer其实主要是对于OPenGL函数的调用，由于我对于这块也不是特别了解，我是在别人的基础上进行了一定的修改，里面参数的修改影响的就是渲染效果。而对于我们要实现的关于旋转缩放的函数其实就比较基础了,这里我还加入了关于缩放范围的控制。
```
		gl.glRotatef(angleX, 0, 1, 0);
        gl.glRotatef(angleY, 1, 0, 0);
        gl.glPopMatrix();

        scale_rember = scale_now * scale;
        if (scaleRange) {
            if (scale_rember > SCALE_MAX) {
                scale_rember = SCALE_MAX;
            }
            if (scale_rember < SCALE_MIN) {
                scale_rember = SCALE_MIN;
            }
        }
        gl.glScalef(scale_rember, scale_rember, scale_rember);
```
3.手势监听
其实对于缩放和旋转的处理和前一篇[Android增强现实（二）-支持拖拽控制进度和伸缩的VrGifView](https://www.jianshu.com/p/abd1772cb061)的处理大同小异，具体大家可以看前一篇博客，而对于陀螺仪的处理其实也比较简单，只不过用的比较少所以比较陌生，步骤也不比较固定。
```
private void initSensor() {
        sensorManager = (SensorManager) mContext.getSystemService(Context.SENSOR_SERVICE);
        gyroscopeSensor = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
        sensorEventListener = new SensorEventListener() {
            @Override
            public void onSensorChanged(SensorEvent sensorEvent) {
                if (sensorEvent.sensor.getType() == Sensor.TYPE_GYROSCOPE) {
                    if (timestamp != 0) {
                        final float dT = (sensorEvent.timestamp - timestamp) * NS2S;
                        stlRenderer.angleX += sensorEvent.values[0] * dT * 180.0f % 360.0f;
                        stlRenderer.angleY += sensorEvent.values[1] * dT * 180.0f % 360.0f;
                        stlRenderer.requestRedraw();
                        requestRender();
                    }
                    timestamp = sensorEvent.timestamp;
                }
            }

            @Override
            public void onAccuracyChanged(Sensor sensor, int accuracy) {

            }
        };
        sensorManager.registerListener(sensorEventListener, gyroscopeSensor, SensorManager
                .SENSOR_DELAY_GAME);
    }
```

### 总结
其实相较于前一篇的对于GIF图的处理，这里技术上的考虑不是特别多，主要是对于3D文件STL格式的学习，OpenGL基础知识的学习，还有陀螺仪传感器使用的学习。

这里对于STL文件的读取还有Renderer中OpenGL的使用参考学习了以下资料，大家感兴趣的可以去查看学习：

>1.[一个不错的STL解析器，支持贴纹理，坐标系等](https://github.com/zhe8300975/STLShowView)
2.[Android OpenGL入门系列，一个不错的系列入门文章](https://github.com/zhe8300975/STLShowView)
3.[Android OpenGL入门系列](https://www.jianshu.com/nb/8716340)
