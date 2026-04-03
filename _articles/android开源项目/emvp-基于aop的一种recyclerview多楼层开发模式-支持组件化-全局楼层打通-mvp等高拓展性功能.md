---
title: "前言"
category: "Android开源项目"
category_slug: "android开源项目"
source_name: "EMvp-基于AOP的一种RecyclerView多楼层开发模式，支持组件化，全局楼层打通，MVP等高拓展性功能"
sort_key: 0017
---
### 前言
RecyclerView作为Google替代ListView的一个组件，其强大的拓展性和性能，现在已经成为无数App核心页面的主体框架。RecyclerView的开发模式一般来说都是多Type类型的ViewHolder——后面就称为楼层(感觉很形象)。但是使用多了，许多问题就暴露出来了，经常考虑有这么几个问题：  

* 1. 如何更便捷的使用Adapter和ViewHolder的开发模式？  
* 2. 如何和他人的楼层做到楼层的复用？
* 3. 如何做到全局楼层的打通？
* 4. 楼层本身如何做到逻辑闭合,做到MVP的组件化模式？  

### 功能特性
* 基于编译期注解，不影响性能
* 使用简单，楼层耦合度低
* 代码侵入性低
* 支持全局楼层打通，多人楼层打通
* 楼层支持点对点MVP模式
* 事件中心模式，楼层只是事件的传递者。
* 生命周期监听，支持逻辑的生命周期感知。
* 丰富的API，支持多方面拓展。
* 提供组件化工程使用方案
* 不用每次再写Adapter了～

### 项目地址
[EMvp](https://github.com/DrownCoder/EMvp)
>欢迎Star👏～
>欢迎提issue讨论～

### 使用方式
这里就介绍一下基于自己对于RecyclerView的理解，开发的一款基于AOP的，适用于多楼层模式的RecyclerView的开发框架。
#### 核心注解
```
@Documented()
// 表示是基于编译时注解的
@Retention(RetentionPolicy.CLASS)
// 表示可以作用于成员变量，类、接口
@Target(ElementType.TYPE)
public @interface ComponentType {
    //ComponentId
    int value() default -1;

    //LayoutId，当为ViewHolder类型需要
    int layout() default -1;
    //组件化项目时，注解父View，通过LayoutInflater创建布局
    Class view() default Object.class;

    //是否利用反射创建，默认打开的(复杂的，性能相关的，数量大的当然建议关闭咯)
    boolean autoCreate() default true;

    //楼层绑定的类，通过类来寻找楼层的可用范围
    Class attach() default Object.class;
}

```
#### 一.单样式列表
##### 1.定义楼层（支持三种模式）
* 继承Component类型
```
@ComponentType(
        value = ComponentId.SIMPLE,
        layout = R.layout.single_text
)
public class SimpleVH extends Component {
    public SimpleVH(Context context, View itemView) {
        super(context, itemView);
    }

    @Override
    public void onBind(int pos, Object item) {
    }
    
    @Override
    public void onUnBind() {
    }
}

```
* 继承原生ViewHolder类型
```
@ComponentType(
        value = PersonId.VIEWHOLDER,
        layout = R.layout.person_item_layout
)
public class PersonVH extends RecyclerView.ViewHolder implements IComponentBind<PersonModel> {
    private TextView tvName;

    public PersonVH(View itemView) {
        super(itemView);
        tvName = itemView.findViewById(R.id.tv_name);
    }

    @Override
    public void onBind(int pos, PersonModel item) {
        tvName.setText(item.name);
    }

    @Override
    public void onUnBind() {
    }
}
```
* 自定义View类型
```
@ComponentType(PersonId.CUSTOM)
public class CustomView extends LinearLayout implements IComponentBind<PersonModel> {
    public CustomView(Context context) {
        super(context);
        LayoutInflater.from(context).inflate(R.layout.cutom_view_vh, this, true);
        setBackgroundColor(Color.BLACK);
    }

    @Override
    public void onBind(int pos, PersonModel item) {
    }

    @Override
    public void onUnBind() {

    }
}
```
很清晰，不用再每次在复杂的`if else`中寻找自己楼层对应的布局文件。(熟悉的人应该都懂)
**注意：**
>1. value:楼层的唯一标示，int型  
>2. layout:楼层的布局文件
>3. 继承ViewHolder和自定义View类型需要实现`IComponentBind`接口即可

**对于R文件不是常量在组件化时遇到的问题的解决方案** [Wiki](https://github.com/DrownCoder/EMvp/wiki/%E7%BB%84%E4%BB%B6%E5%8C%96%E9%A1%B9%E7%9B%AE%E4%B8%ADR%E6%96%87%E4%BB%B6%E6%97%A0%E6%B3%95%E4%BD%BF%E7%94%A8)
这里没有选用butterknife将R文件复制一份成R2的方式，我个人感觉不是特别优雅，最终我选择的是在注解中增加一种View类型的注解，可以在注解中注解父View的Class，然后在构造函数通过LayoutInflater加入布局文件。
```
@ComponentType(
        value = ComponetId.BANNER,
        view = FrameLayout.class
)
public BannerVH(Context context, View itemView) {
        super(context, itemView);
        fgContainer = (FrameLayout) itemView;
        //再利用LayoutInflater
        LayoutInflater.from(context).inflate()
    }
```
##### 2.定义Model
```
@BindType(ComponentId.SIMPLE)
public class SimpleModel {
    
}
```
**BindType**:当是单样式时，model直接注解对应的楼层的唯一标示，int型

##### 3.绑定RecyclerView
```
@Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.common_layout);
        mRcy = findViewById(R.id.rcy);
        mRcy.setLayoutManager(new LinearLayoutManager(this));
        new ToolKitBuilder<>(this, mData).build().bind(mRcy);
    }
```
使用对应的API，利用build()方法构建SlotsContext实体最后利用`bind()`方法绑定ReyclerView.
#### 二.多楼层模式
1.定义ViewHolder(同前一步)
2.多样式判断逻辑(两种方式)
##### 2.1 Model实现HandlerType接口处理逻辑
```
public class CommonModel implements HandlerType {
    public int pos;
    public String tips;
    public String eventId;

    @Override
    public int handlerType() {
        if (pos > 8) {
            pos = pos % 8;
        }
        switch (pos) {
            case 1:
                return ComponentId.VRCY;
            case 3:
                return ComponentId.DIVIDER;
            case 4:
                return ComponentId.WEBVIEW;
            case 5:
                return ComponentId.TEXT_IMG;
            case 6:
                return ComponentId.IMAGE_TWO_VH;
            case 7:
                return ComponentId.IMAGE_VH;
            case 8:
                return ComponentId.USER_INFO_LAYOUT;
        }
        return ComponentId.VRCY;
    }
}
```

返回定义的ItemViewType，这里封装在Model内部，是由于平时我们总是将java中的Model当作一个JavaBean，而导致我们赋予Model的职责过于轻，所以就会出现更多的其实和Model紧密相关的逻辑放到了Activity，Presenter或者别的地方，但是其实当我们将Model当作数据层来看待，其实可以将许多与Model紧密相关的逻辑放到Model中，这样我们其实单模块的逻辑内聚度就很高，便于我们理解。
(这里思路其实来源于IOS开发中的**胖Model**的概念，大家可以Goolge一下)
>**好处**：当我们需要确定楼层之间和Model的关系，直接按住ctrl，进入Model类，一下就可以找到相关逻辑。

##### 2.2 实现IModerBinder接口自定义处理类
一款好的框架肯定是对修改关闭，对拓展开放的，当我们认为放到Model中处理过于粗暴，或者Model中已经有过多的逻辑了，我们也可以将逻辑抽出来，实现IModerBinder接口。
```
public interface IModerBinder<T> {
    int getItemType(int pos, T t);
}
```
对应的利用`ToolKitBuilder.setModerBinder(IModerBinder<T> moderBinder)`构建即可。例如：
```
.setModerBinder(new ModelBinder<PersonModel>() {
                    @Override
                    protected int bindItemType(int pos, PersonModel obj) {
                    	//处理Type的相关逻辑
                       return type;
                    }
                })
```
### 个人模式
当涉及到大型项目时，多人协作往往是一个问题，当所有人都维护一套ComponentId，合并代码时解决冲突往往是很大的问题，并且不可能所有的楼层都是全局打通的类型，所以这里提供一种个人开发模式。
### 用法
* 1.使用attach注解，绑定对应class
```
@ComponentType(
        value = PersonId.VIEWHOLDER,
        layout = R.layout.person_item_layout,
        //class类型，对应到映射表的key
        attach = PersonModel.class
)
public class PersonVH extends RecyclerView.ViewHolder implements IComponentBind<PersonModel> {
    private TextView tvName;

    public PersonVH(View itemView) {
        super(itemView);
        tvName = itemView.findViewById(R.id.tv_name);
    }

    @Override
    public void onBind(int pos, PersonModel item) {
        //tvName.findViewById(R.id.tv_name);
        tvName.setText(item.name);
    }

    @Override
    public void onUnBind() {

    }
}
```
* 2.调用SlotContext.attachRule绑定对应的Class
```
SlotContext slotContext =
                new ToolKitBuilder<PersonModel>(this)
                        //注册绑定的类型，对应获取映射表
                        .attachRule(PersonModel.class).build();
```
### 进阶使用
项目利用Build模式构建SlotContext实体，SlotContext原理基于Android中的Context思想，作为一个全局代理的上下文对象，通过SlotContext，我们可以获取对应的类，进而实现对应类的获取和通信。
#### 避免反射创建
框架本身利用反射进行创建，内部利用`LruCache`对反射对构造器进行缓存，优化反射性能。如果想要避免反射对创建，也是可以自定义创建过程。
```
@ComponentType(
            value = PersonId.INNER,
            view = TextView.class,
            //注解不使用反射
            autoCreate = false
    )
    public static class InnerVH extends RecyclerView.ViewHolder implements IComponentBind<PersonModel> {
       ....
    }
```
可以将不需要反射创建对ViewHolder的`autoCreate=false`，然后通过`ToolKitBuilder. setComponentFactory()`自定义创建过程。
具体方式->[Wiki](https://github.com/DrownCoder/EMvp/wiki/%E4%BC%98%E5%8C%96%E5%8F%8D%E5%B0%84%E5%88%9B%E5%BB%BA)
#### 事件中心
事件中心其实本质就是一个继承于`View.OnClickListener`的类，**所有和ViewHolder本身无关的事件**，统一传递给事件中心，再由事件中心处理，对应于一条准则：
>ViewHolder只是一个专注于展示UI的壳，只做事件的传递者，不做事件的处理者。

**使用方式：**
```
@ComponentType(
        value = ComponetId.SINGLE_TEXT,
        layout = R.layout.single_text
)
public class TextVH extends Component<Text> implements InjectCallback {
    private TextView tv;
    private View.OnClickListener onClickListener;
    public TextVH(Context context, View itemView) {
        super(context, itemView);
        tv = (TextView) itemView;
    }
    @Override
    public void onBind(int pos, Text item) {
        tv.setText(item.title);
        //此处所有的数据和事件类型通过setTag传出
        tv.setTag(item.eventId);
        tv.setOnClickListener(onClickListener);
    }
    @Override
    public void onUnBind() {

    }
    @Override
    public void injectCallback(View.OnClickListener onClickListener) {
        this.onClickListener = onClickListener;
    }
}
```
仿照**依赖注入**的思想，只不过代码侵入性没有那么强，当然只能在onBind的时候才能绑定，构造函数的时候，事件中心对象还没有注入进来。
* 1. ViewHolder实现InjectCallback接口，在onBind生命周期就可以拿到事件中心对象。
* 2. 通过View.setTag，将事件类型(int型等，唯一性)和相关需要的数据传出。

事件中心的思想就是：ViewHolder单纯的只传递事件，完全由数据驱动事件，View不感知事件类型，也就是说，这个ViewHolder的事件是**可变的**！
#### MVP的拆分
关于MVP是什么这里就不多讲了，这里讲一讲MVP的拆分，常规的MVP我们经常做的就是一个P完成所有的逻辑，但是这时带来的问题就时P层过于大，这时我的理解就是对P进行拆分，具体拆分的粒度要根据不同的业务场景来区分(这个就比较考验开发者对于设计模式的理解)。而ViewHolder自身可以完成一套MVP体系，想一想，当一个特殊的楼层，涉及复杂的业务逻辑，这时完全将这个楼层拆分成MVP模式，这时其他页面需要使用的时候，只需要new对应的MVP即可。
```
@Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        ...
        slotContext = new ToolKitBuilder<>(this, mData).build();
        //1.注册对应的逻辑类
        slotContext.registerLogic(new CommonLogic(slotContext));
        ...
    }


@ComponentType(value = ComponentId.TEXT_IMG)
//2.注解对应的逻辑类
@ILogic(CommonLogic.class)
//3.实现IPresenterBind接口
public class TextImgLayout extends LinearLayout implements IComponentBind<CommonModel>,IPresenterBind<CommonLogic> {
    private View root;
    private TextView tvInfo;
    private CommonLogic logic;
	...
    @Override
    public void onBind(int pos, CommonModel item) {
        tvInfo.setOnClickListener(new OnClickListener() {
            @Override
            public void onClick(View v) {
                if (logic != null) {
                //对应的P，处理业务逻辑
                    logic.pageTransfer();
                }
            }
        });
    }
    ...
    @Override
    public void injectPresenter(CommonLogic commonLogic) {
        this.logic = commonLogic;
    }
}
```
对应的需要三步：
* 1. `slotContext.registerLogic(IPresenter presener)`，这里IPresenter只是一个空接口，用于表明这是一个逻辑层的类。
* 2. 在ViewHolder利用@ILogic注解对应的P的Class
* 3. ViewHolder实现IPresenterBind接口，注入注册给SlotContext对应的Presenter.
#### 生命周期感知
无论是Presenter还是任何其他类，当脱离的Activity，对于生命周期的感知时非常重要的，所以SlotContext提供的有两个API
```
pushLife(ILifeCycle lifeCycle)
pushGC(IGC gc)
```
需要感知生命周期，或者仅仅感知OnDestroy的类，只需实现相应的接口，并利用api注册观察者即可。
#### MIX模式，多楼层打通
对于多楼层打通，我们需要利用ToolKitBuilder实现IMixStrategy策略。
```
public interface IMixStrategy<T> {
    //通过type得到真正的映射表中的ComponentId
    int getComponentId(int type);

    //通过Type确定对应的映射表
    Class<?> attachClass(int type);

    //传入ViewHolder的Bind中的实体类
    Object getBindItem(int pos, T t);
}
```
具体方案->[Wiki](https://github.com/DrownCoder/EMvp/wiki/%E5%A4%9A%E4%BA%BAMIX%E6%A8%A1%E5%BC%8F)
#### ToolKitBuilder的构造函数
```
public ToolKitBuilder(Context context, List<T> data)
public ToolKitBuilder(Context context)
```
#### ToolKitBuilder的API
| 方法名 | 描述 | 备注 |
| ------ | ------ | ------ |
| setData(List<T> data) | 设置绑定的数据集 | 空对象，对应的构造的size=0 |
| setModerBinder(IModerBinder<T> moderBinder) | 处理多样式时Model对应的Type | 处理优先级优先于HandlerType和注解BindType |
| setEventCenter(View.OnClickListener onClickListener) | 设置事件中心 | ViewHolder的事件绑定后都会回调到这个事件中心 |
| setComponentFactory(CustomFactory componentFactory) | 设置自定义创建ViewHolder的工厂 | 可以自定义创建三种类型 |
| setMixStrategy(IMixStrategy<T> mixStrategy) | 设置混合模式处理策略 | 多人楼层打通 |
| attachRule(Class<?> clazz) | 注册楼层映射表 | 个人模式和混合模式 |
| SlotContext<T> build() | 构建出SlotContext对象 |  |
#### SlotContext的构造函数
```
public SlotContext(Context context, List<T> data)
public SlotContext(ToolKitBuilder<T> builder)
```
#### SlotContext的API
| 方法名 | 描述 | 备注 |
| ------ | ------ | ------ |
| Context getContext() | 获取Context对象 |  |
| setData(List<T> data) | 绑定数据集 | 这里不会刷新数据，仅仅是设置 |
| notifyDataSetChanged() | 刷新数据 | 只提供了全局刷新的方式，局部刷新可以通过获取Adapter使用 |
| attachRule(Class<?> clazz) | 注册楼层映射表 | 个人模式和混合模式 |
| registerLogic(IPresent logic) | 注册Presenter逻辑 | 可注册多个，需要实现IPresenter空接口 |
| obtainLogic(Class<?> clazz) | 获取对应注册的Presenter实例 | 以class作为key |
| bind(RecyclerView rcy) | 绑定Adapter | 会重新创建Adapter并绑定 |
| RecyclerView.Adapter getAdapter() | 获取Adapter |  |
| pushLife(ILifeCycle lifeCycle) | 注册任何对象监听生命周期 | 实现ILifeCycler接口 |
| pushGC(IGC gc) | 监听Destroy生命周期 |  |

### 更多拓展
更多使用方式详见[Wiki](https://github.com/DrownCoder/EMvp/wiki)
### 项目源码解析
[Python自动生成10000个java类使用APT注解后引发的问题](https://www.jianshu.com/p/0be28a7b565b)
>项目地址：[EMvp](https://github.com/DrownCoder/EMvp)
>欢迎Star👏
>欢迎大家提issues提意见～





