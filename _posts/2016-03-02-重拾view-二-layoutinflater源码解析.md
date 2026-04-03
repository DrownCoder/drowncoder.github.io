---
title: 【重拾View(二)】——LayoutInflater源码解析
date: 2018-10-13 14:56:13+08:00
categories: ["Android源码分析"]
source_name: "【重拾View(二)】——LayoutInflater源码解析"
jianshu_views: 640
jianshu_url: "https://www.jianshu.com/p/86696bda40f3"
---
>1.[【重拾View(一)】——setContentView()源码解析](https://www.jianshu.com/p/9e1cf127f0ae)
>2.[【重拾View(二)】——LayoutInflater源码解析](https://www.jianshu.com/p/86696bda40f3)
>3.[【重拾View(三)】——LayoutInflater中Factory源码解析](https://www.jianshu.com/p/281d87f17c66)
### 前言
看了前一篇文章[【重拾View(一)】——setContentView()源码解析](https://www.jianshu.com/p/9e1cf127f0ae)我们了解到了Activity加载布局到过程，但是对于View的创建过程还需要进一步的了解。熟悉Android的应该都清楚，Android布局的一大特点就是XML文件，我们通过编写XML文件，便可以轻松的创建我们需要的View，这也是和IOS开发的一个很大的区别。但是当我们编写完一个XML文件，还需要生成对应可绘制的View对象，这时我们经常使用的方法便是LayoutInflater的`inflate()`方法。无论是我们自定义View通过还是Fragment还是我们上篇文章分析的Activity加载布局的过程，实质都是使用这种方式创建View。所以本篇博客便对LayoutInflater的源码进行分析。
### 创建对象
要获取LayoutInflater对象我们经常使用的有三种方式：
>1. Context.getSystemService(Context.LAYOUT_INFLATER_SERVICE) ;
>2. LayoutInflater.from(context);
>3. Activity.getLayoutInflater()；

```
public static LayoutInflater from(Context context) {
        LayoutInflater LayoutInflater =
                (LayoutInflater) context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
        if (LayoutInflater == null) {
            throw new AssertionError("LayoutInflater not found.");
        }
        return LayoutInflater;
    }
```
```
//Activity.java
	@NonNull
    public LayoutInflater getLayoutInflater() {
        return getWindow().getLayoutInflater();
    }
 //PhoneWindow.java
    @Override
    public LayoutInflater getLayoutInflater() {
        return mLayoutInflater;
    }
    
    public PhoneWindow(Context context) {
        super(context);
        mLayoutInflater = LayoutInflater.from(context);
    }
```
通过上面的源码，其实我们可以发现上面三种方式的最终效果都是`context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);`
### inflate源码分析
我们最常用的`inflate`方法其实有两种
```
public View inflate(@LayoutRes int resource, @Nullable ViewGroup root) {
        return inflate(resource, root, root != null);
    }
    
public View inflate(@LayoutRes int resource, @Nullable ViewGroup root, boolean attachToRoot) {
        final Resources res = getContext().getResources();
        if (DEBUG) {
            Log.d(TAG, "INFLATING from resource: \"" + res.getResourceName(resource) + "\" ("
                    + Integer.toHexString(resource) + ")");
        }
        //获取xml解析器
        final XmlResourceParser parser = res.getLayout(resource);
        try {
        		//解析xml文件
            return inflate(parser, root, attachToRoot);
        } finally {
            parser.close();
        }
    }
```
可以看到inflate方法其实就是做了两步：
1. 创建XML解析器  
2. 解析XML文件成View并返回
这里面我们要注意一下三个参数的传参，第一个当然就是我们的XML的id，第二个一般是我们传入的父View，第三个boolean注意当默认我们没有传值的时候，默认是`root != null`，也就是父View不为空则是`true`，为空便是`false`。
接下来我们来看一下inflate方法源码，看看是怎么解析xml文件的。
```
public View inflate(XmlPullParser parser, @Nullable ViewGroup root, boolean attachToRoot) {
        //1.线程同步
        synchronized (mConstructorArgs) {
            Trace.traceBegin(Trace.TRACE_TAG_VIEW, "inflate");

            final Context inflaterContext = mContext;
            final AttributeSet attrs = Xml.asAttributeSet(parser);
            Context lastContext = (Context) mConstructorArgs[0];
            mConstructorArgs[0] = inflaterContext;
            //2.首先将root设置为result
            View result = root;

            try {
                // Look for the root node.
                int type;
                //3.遍历寻找布局的根结点
                while ((type = parser.next()) != XmlPullParser.START_TAG &&
                        type != XmlPullParser.END_DOCUMENT) {
                    // Empty
                }
                //4.如果找到的不是根结点，则异常
                if (type != XmlPullParser.START_TAG) {
                    throw new InflateException(parser.getPositionDescription()
                            + ": No start tag found!");
                }
                //5.获取根结点的名称
                final String name = parser.getName();

                if (DEBUG) {
                    System.out.println("**************************");
                    System.out.println("Creating root view: "
                            + name);
                    System.out.println("**************************");
                }
                //6.如果是merge节点
                if (TAG_MERGE.equals(name)) {
                    //root不能为null，attachToRoot不能为false
                    if (root == null || !attachToRoot) {
                        throw new InflateException("<merge /> can be used only with a valid "
                                + "ViewGroup root and attachToRoot=true");
                    }
                    //7.解析merge节点下的
                    rInflate(parser, root, inflaterContext, attrs, false);
                } else {
                    // Temp is the root view that was found in the xml
                    //8.根据解析得到的节点名创建View
                    final View temp = createViewFromTag(root, name, inflaterContext, attrs);

                    ViewGroup.LayoutParams params = null;

                    if (root != null) {
                        if (DEBUG) {
                            System.out.println("Creating params from root: " +
                                    root);
                        }
                        // Create layout params that match root, if supplied
                        //9.根据父View创建LayoutParams
                        params = root.generateLayoutParams(attrs);
                        if (!attachToRoot) {
                            // Set the layout params for temp if we are not
                            // attaching. (If we are, we use addView, below)
                            //10.如果不是attachToRoot,则将LayoutParam设置给View的属性中
                            temp.setLayoutParams(params);
                        }
                    }

                    if (DEBUG) {
                        System.out.println("-----> start inflating children");
                    }

                    // Inflate all children under temp against its context.
                    //11.递归解析子布局
                    rInflateChildren(parser, temp, attrs, true);

                    if (DEBUG) {
                        System.out.println("-----> done inflating children");
                    }

                    // We are supposed to attach all the views we found (int temp)
                    // to root. Do that now.
                    if (root != null && attachToRoot) {
                        //12.root不为null，并且attachToRoot，则将View加入到父View中，并将LayoutParams设置
                        root.addView(temp, params);
                    }

                    // Decide whether to return the root that was passed in or the
                    // top view found in xml.
                    if (root == null || !attachToRoot) {
                        //13.如果root为null或者attachToRoot为false，则返回解析得到的View
                        result = temp;
                    }
                }

            } catch (XmlPullParserException e) {
                final InflateException ie = new InflateException(e.getMessage(), e);
                ie.setStackTrace(EMPTY_STACK_TRACE);
                throw ie;
            } catch (Exception e) {
                final InflateException ie = new InflateException(parser.getPositionDescription()
                        + ": " + e.getMessage(), e);
                ie.setStackTrace(EMPTY_STACK_TRACE);
                throw ie;
            } finally {
                // Don't retain static reference on context.
                mConstructorArgs[0] = lastContext;
                mConstructorArgs[1] = null;

                Trace.traceEnd(Trace.TRACE_TAG_VIEW);
            }
            //14.返回解析得到的View或者父View
            return result;
        }
    }
```
首先可以看到，inflate方法是做了线程同步的，为了保证线程安全。紧接着在**注释2**处可以看到，首先将`rootView`赋值给了`result`，所以这里我们需要明白:
>有时候我们通过`inflate`方法加载的xml文件得到的View不一定是我们xml中的父布局，可能是我们传入的`rootView`，如果不明白这个，轻易的就将View**强转**成我们认为的xml中的父布局，便会产生**类型转换异常**。

接下来的**注释3**和**注释4**可以一起理解，是对于**XML**文件的规则的校验，可以看到这里通过`while`循环查找布局中的根结点，当没找到规定的根结点，在**注释4**处当然便会抛没有找到根结点的异常。
紧接着在**注释5**处可以看到在找到根结点后，通过`getName`方法获取根结点的名称，这时我们在**注释6**处就有一个关键的判断了，是关于对于`merge`结点的判断逻辑。
```
if (TAG_MERGE.equals(name)) {
                    //root不能为null，attachToRoot不能为false
                    if (root == null || !attachToRoot) {
                        throw new InflateException("<merge /> can be used only with a valid "
                                + "ViewGroup root and attachToRoot=true");
                    }
                    //7。解析merge节点下的
                    rInflate(parser, root, inflaterContext, attrs, false);
                }
```
这里可以看到如果`xml`的根结点是`merge`标签，下面有两个非常重要的判断条件，**root==null|| !attachToRoot**，当条件成立，便会抛出我们使用`merge`标签经常遇到的异常。这里细化分析一下，我们`root`和`attachToRoot`有多种可能。
1. 没有传attachToRoot
	1.1 root=null,则attachToRoot为false
	》这时会抛异常
	1.2 root!=null,则attahcToRoot为true
	》允许解析merge标签
2.传入了attachToRoot
	2.1 root=null,attachToRoot=true
	》抛异常
	2.2 roo!=null,attachToRoot=true
	》允许解析merge标签
	2.3 root=null,attachToRoot=false
	》抛异常
	2.4 root!=null,attachToRoot=false
	》抛异常
这时这个逻辑就比较清晰了，当我们使用`merge`标签时，我们的`root`一定不能传入`null`，`attahToRoot`要不不传，传入只能传入`true`，所以这时就可以证明我们使用`merge`标签的规则了：
>**使用merge标签必须有父布局，并且attachToRoot一定为true**

当完成这个判断后面便执行`rInflate(parser, root, inflaterContext, attrs, false);`方法，解析`merge`标签下的布局。关于`rInflate`方法后面我们后面再分析。
```
final View temp = createViewFromTag(root, name, inflaterContext, attrs);
```
当我们的根布局不是一个`merge`标签，这时在**注释8**处，便通过`createViewFromTag`方法将我们传入的xml中的父布局创建出了我们需要的`View`对象。关于`createViewFromTag`后面我们再分析。
当创建完父布局的View后，接下来还是和`root`和`attachToRoot`绕弯弯。
```
if (root != null) {
                        if (DEBUG) {
                            System.out.println("Creating params from root: " +
                                    root);
                        }
                        // Create layout params that match root, if supplied
                        //9。根据父View创建LayoutParams
                        params = root.generateLayoutParams(attrs);
                        if (!attachToRoot) {
                            // Set the layout params for temp if we are not
                            // attaching. (If we are, we use addView, below)
                            //10。如果不是attachToRoot,则将LayoutParam设置给View的属性中
                            temp.setLayoutParams(params);
                        }
                    }
```
有了上面分析的基础这里思路就比较清晰了，可以看到当`root`不为null,并且`attachToRoot`为false，则将根据root创建的LayoutParams设置给创建出来的`View`-temp。所以当`root`不为null的情况，当我们传入`attachToRoot=false`，则会把`root`的`LayoutParam`设置给创建出来的`TempView`，当传入的`attachToRoot=true`，则**此处**不会设置（注意是此处！）。
紧接着在**注释11**处，解析完根结点后，调用`rInflateChildren`方法递归开始解析子布局。
```
final void rInflateChildren(XmlPullParser parser, View parent, AttributeSet attrs,
            boolean finishInflate) throws XmlPullParserException, IOException {
        rInflate(parser, parent, parent.getContext(), attrs, finishInflate);
    }
```
其实可以看到`rInflateChildren`方法实质调用的还是`rInflate`方法，所以后面我们会一起分析。
```
if (root != null && attachToRoot) {
                        //12。root不为null，并且attachToRoot，则将View加入到父View中，并将LayoutParams设置
                        root.addView(temp, params);
                    }

                    // Decide whether to return the root that was passed in or the
                    // top view found in xml.
                    if (root == null || !attachToRoot) {
                        //13。如果root为null或者attachToRoot为false，则返回解析得到的View
                        result = temp;
                    }
```
这时会看到一个很重要的一点，又和`root`和`attachToRoot`这两个变量打交道了，不仔细梳理的话很容易被这两个变量搞混乱。这里看到如果root不为null，并且attachToRoot，则将View加入到父View中，并将LayoutParams设置（在addView中会设置）。并且如果root为null或者attachToRoot为false，会将result设置为解析的temp,则返回解析得到的View（最初是将root设置给了result）。
到此我们的`infalte`方法其实已经分析完了，这里我们可以梳理一下关于`root`和`attachToRoot`的逻辑。
1. root为null
》如果root为null，则返回的就是xml中的父布局，并且该View也是没有LayoutParams参数
2. root不为null
        2.1 attachToRoot=true
	》返回的是root，此时xml已经被加入到了rootView中
	2.2 attachToRoot=false
	》返回的是xml的父布局，但是此时xml的父布局没有被加入到root中，只是一个单纯的View，但是它有LayoutParams，是root类型的LayoutParams.

### rInflate方法解析
```
void rInflate(XmlPullParser parser, View parent, Context context,
            AttributeSet attrs, boolean finishInflate) throws XmlPullParserException, IOException {
		  //获取深度
        final int depth = parser.getDepth();
        int type;
        boolean pendingRequestFocus = false;

        while (((type = parser.next()) != XmlPullParser.END_TAG ||
                parser.getDepth() > depth) && type != XmlPullParser.END_DOCUMENT) {

            if (type != XmlPullParser.START_TAG) {
                continue;
            }

            final String name = parser.getName();

            if (TAG_REQUEST_FOCUS.equals(name)) {
                pendingRequestFocus = true;
                consumeChildElements(parser);
            } else if (TAG_TAG.equals(name)) {
                //1。解析tag标签，也就是View.setTag
                parseViewTag(parser, parent, attrs);
            } else if (TAG_INCLUDE.equals(name)) {
                //2。解析include标签
                if (parser.getDepth() == 0) {
                    throw new InflateException("<include /> cannot be the root element");
                }
                parseInclude(parser, context, parent, attrs);
            } else if (TAG_MERGE.equals(name)) {
                //3。merge必须为根结点
                throw new InflateException("<merge /> must be the root element");
            } else {
                //4。创建当前节点的View
                final View view = createViewFromTag(parent, name, context, attrs);
                final ViewGroup viewGroup = (ViewGroup) parent;
                final ViewGroup.LayoutParams params = viewGroup.generateLayoutParams(attrs);
                //递归深度继续解析
                rInflateChildren(parser, view, attrs, true);
                viewGroup.addView(view, params);
            }
        }

        if (pendingRequestFocus) {
            parent.restoreDefaultFocus();
        }

        if (finishInflate) {
            parent.onFinishInflate();
        }
    }
```
可以看到这里，首先获取xml的深度，然后依旧是`while`循环解析，所以下面就是各种标签情况的处理了。
首先看到**注释1**处，可以看到是对于`tag`标签到解析，当时`tag`标签，则调用`parseViewTag`方法。
```
private void parseViewTag(XmlPullParser parser, View view, AttributeSet attrs)
            throws XmlPullParserException, IOException {
        final Context context = view.getContext();
        final TypedArray ta = context.obtainStyledAttributes(attrs, R.styleable.ViewTag);
        final int key = ta.getResourceId(R.styleable.ViewTag_id, 0);
        final CharSequence value = ta.getText(R.styleable.ViewTag_value);
        //其实就是setTag...
        view.setTag(key, value);
        ta.recycle();

        consumeChildElements(parser);
    }
```
可以看到，这个方法的本质就是我们常用的`setTag`方法，也就是说我们可以有以下这种写法(虽然不常用)。
```
<Button
        android:id="@+id/tag_btn"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="自定义带监听事件的通知">

        <tag
            android:id="@+id/tag_id"
            android:value="@string/app_name" />

    </Button>
```
接下来解析的是我们常用的`include`标签，首先在**注释2**处，我们可以看到，`include`是不能再xml的深度=0的，应该也没人会把include作为xml的根结点吧。。。紧接着便调用`parseInclude`方法解析`include`标签内的布局文件。
```
private void parseInclude(XmlPullParser parser, Context context, View parent,
            AttributeSet attrs) throws XmlPullParserException, IOException {
        int type;

        if (parent instanceof ViewGroup) {
            // Apply a theme wrapper, if requested. This is sort of a weird
            // edge case, since developers think the <include> overwrites
            // values in the AttributeSet of the included View. So, if the
            // included View has a theme attribute, we'll need to ignore it.
            final TypedArray ta = context.obtainStyledAttributes(attrs, ATTRS_THEME);
            final int themeResId = ta.getResourceId(0, 0);
            final boolean hasThemeOverride = themeResId != 0;
            if (hasThemeOverride) {
                context = new ContextThemeWrapper(context, themeResId);
            }
            ta.recycle();

            // If the layout is pointing to a theme attribute, we have to
            // massage the value to get a resource identifier out of it.
            int layout = attrs.getAttributeResourceValue(null, ATTR_LAYOUT, 0);
            if (layout == 0) {
                final String value = attrs.getAttributeValue(null, ATTR_LAYOUT);
                if (value == null || value.length() <= 0) {
                    throw new InflateException("You must specify a layout in the"
                            + " include tag: <include layout=\"@layout/layoutID\" />");
                }

                // Attempt to resolve the "?attr/name" string to an attribute
                // within the default (e.g. application) package.
                layout = context.getResources().getIdentifier(
                        value.substring(1), "attr", context.getPackageName());

            }

            // The layout might be referencing a theme attribute.
            if (mTempValue == null) {
                mTempValue = new TypedValue();
            }
            if (layout != 0 && context.getTheme().resolveAttribute(layout, mTempValue, true)) {
                layout = mTempValue.resourceId;
            }

            if (layout == 0) {
                final String value = attrs.getAttributeValue(null, ATTR_LAYOUT);
                throw new InflateException("You must specify a valid layout "
                        + "reference. The layout ID " + value + " is not valid.");
            } else {
                //把inflate方法又写了一遍，其实感觉Google这里的写法是可以优化的。。。。
                final XmlResourceParser childParser = context.getResources().getLayout(layout);

                try {
                    final AttributeSet childAttrs = Xml.asAttributeSet(childParser);

                    while ((type = childParser.next()) != XmlPullParser.START_TAG &&
                            type != XmlPullParser.END_DOCUMENT) {
                        // Empty.
                    }

                    if (type != XmlPullParser.START_TAG) {
                        throw new InflateException(childParser.getPositionDescription() +
                                ": No start tag found!");
                    }

                    final String childName = childParser.getName();

                    if (TAG_MERGE.equals(childName)) {
                        // The <merge> tag doesn't support android:theme, so
                        // nothing special to do here.
                        rInflate(childParser, parent, context, childAttrs, false);
                    } else {
                        final View view = createViewFromTag(parent, childName,
                                context, childAttrs, hasThemeOverride);
                        final ViewGroup group = (ViewGroup) parent;

                        final TypedArray a = context.obtainStyledAttributes(
                                attrs, R.styleable.Include);
                        final int id = a.getResourceId(R.styleable.Include_id, View.NO_ID);
                        final int visibility = a.getInt(R.styleable.Include_visibility, -1);
                        a.recycle();

                        // We try to load the layout params set in the <include /> tag.
                        // If the parent can't generate layout params (ex. missing width
                        // or height for the framework ViewGroups, though this is not
                        // necessarily true of all ViewGroups) then we expect it to throw
                        // a runtime exception.
                        // We catch this exception and set localParams accordingly: true
                        // means we successfully loaded layout params from the <include>
                        // tag, false means we need to rely on the included layout params.
                        ViewGroup.LayoutParams params = null;
                        try {
                            params = group.generateLayoutParams(attrs);
                        } catch (RuntimeException e) {
                            // Ignore, just fail over to child attrs.
                        }
                        if (params == null) {
                            params = group.generateLayoutParams(childAttrs);
                        }
                        view.setLayoutParams(params);

                        // Inflate all children.
                        rInflateChildren(childParser, view, childAttrs, true);

                        if (id != View.NO_ID) {
                            view.setId(id);
                        }

                        switch (visibility) {
                            case 0:
                                view.setVisibility(View.VISIBLE);
                                break;
                            case 1:
                                view.setVisibility(View.INVISIBLE);
                                break;
                            case 2:
                                view.setVisibility(View.GONE);
                                break;
                        }

                        group.addView(view);
                    }
                } finally {
                    childParser.close();
                }
            }
        } else {
            throw new InflateException("<include /> can only be used inside of a ViewGroup");
        }

        LayoutInflater.consumeChildElements(parser);
    }
```
这里可以看到include标签记载的布局必须是ViewGroup，不然会抛异常，剩下的**仔细看的话会发现其实和inflate方法几乎一摸一样，只不过多了一些属性判断，其实感觉Google这里的写法是可以优化的。。。**
解析完`include`方法后在**注释3**处就是解析`merge`标签，这里可以看到，如果是`merge`标签，便会直接抛异常，当然，在`rInflate`方法其实已经是解析子View的方法了。
>**merge标签只能用于根结点**
```
else {
                //4。创建当前节点的View
                final View view = createViewFromTag(parent, name, context, attrs);
                final ViewGroup viewGroup = (ViewGroup) parent;
                final ViewGroup.LayoutParams params = viewGroup.generateLayoutParams(attrs);
                //递归深度继续解析
                rInflateChildren(parser, view, attrs, true);
                viewGroup.addView(view, params);
            }
```
剩下的就是其他常规View的创建了，利用`createViewFromTag `方法进行创建，创建完后调用`rInflateChildren `继续**递归深度继续解析**，然后加入到父布局中。
最终完成整个XML->View的转换。
### createViewFromTag方法
```
private View createViewFromTag(View parent, String name, Context context, AttributeSet attrs) {
        return createViewFromTag(parent, name, context, attrs, false);
    }
    
View createViewFromTag(View parent, String name, Context context, AttributeSet attrs,
            boolean ignoreThemeAttr) {
        if (name.equals("view")) {
            name = attrs.getAttributeValue(null, "class");
        }

        // Apply a theme wrapper, if allowed and one is specified.
        if (!ignoreThemeAttr) {
            final TypedArray ta = context.obtainStyledAttributes(attrs, ATTRS_THEME);
            final int themeResId = ta.getResourceId(0, 0);
            if (themeResId != 0) {
                context = new ContextThemeWrapper(context, themeResId);
            }
            ta.recycle();
        }

        if (name.equals(TAG_1995)) {
            // Let's party like it's 1995!
            //1。彩蛋，BlinkLayout，好像是为了庆祝1995年的复活节，是一个Layout，包含后，会一闪一闪
            return new BlinkLayout(context, attrs);
        }

        try {
            View view;
            //2。几个工厂，可以通过Activity设置后，自定义创建
            if (mFactory2 != null) {
                view = mFactory2.onCreateView(parent, name, context, attrs);
            } else if (mFactory != null) {
                view = mFactory.onCreateView(name, context, attrs);
            } else {
                view = null;
            }

            if (view == null && mPrivateFactory != null) {
                view = mPrivateFactory.onCreateView(parent, name, context, attrs);
            }

            if (view == null) {
                final Object lastContext = mConstructorArgs[0];
                mConstructorArgs[0] = context;
                try {
                    if (-1 == name.indexOf('.')) {
                        //3。没有.说明是原生系统内的控件
                        view = onCreateView(parent, name, attrs);
                    } else {
                        //4。有.说明是自定义控件
                        view = createView(name, null, attrs);
                    }
                } finally {
                    mConstructorArgs[0] = lastContext;
                }
            }

            return view;
        } catch (InflateException e) {
            throw e;

        } catch (ClassNotFoundException e) {
            final InflateException ie = new InflateException(attrs.getPositionDescription()
                    + ": Error inflating class " + name, e);
            ie.setStackTrace(EMPTY_STACK_TRACE);
            throw ie;

        } catch (Exception e) {
            final InflateException ie = new InflateException(attrs.getPositionDescription()
                    + ": Error inflating class " + name, e);
            ie.setStackTrace(EMPTY_STACK_TRACE);
            throw ie;
        }
    }    
```
>这里我们首先看一个有趣的地方，那就是**注释1**，这里可以算是源码里的**彩蛋**，从名字上也就看出了这个的不一般～，这里提供了一个叫做`BlinkLayout `的控件，好像是为了庆祝1995年的复活节，是一个Layout，包含后，会一闪一闪。

接下来会看到几个工厂的创建，如果我们实现了几个工厂，那么我们就可以自定义View的创建过程，这里关于工厂的内容后面一篇博客会进行分析。
如果是常规的使用，我们一般不会使用自定义工厂这种方式的，所以到后面就是一个关键判断。
```
if (-1 == name.indexOf('.')) {
                        //3。没有.说明是原生系统内的控件
                        view = onCreateView(parent, name, attrs);
                    } else {
                        //4。有.说明是自定义控件
                        view = createView(name, null, attrs);
                    }
```
这里通过标签名时候包含‘.’作为判断依据，如果不包含‘.’则说明是原生系统内的控件，如果包含则是自定义控件。而系统控件执行的`onCreateView`方法，实质也是`createView`方法,只不过加上了"android.view."的前缀
```
protected View onCreateView(String name, AttributeSet attrs)
            throws ClassNotFoundException {
        //最终还是调用的是createView方法，只不过加上了"android.view."的前缀
        return createView(name, "android.view.", attrs);
    }
```
接下来我们来看一下`createView`方法。
```
public final View createView(String name, String prefix, AttributeSet attrs)
            throws ClassNotFoundException, InflateException {
        Constructor<? extends View> constructor = sConstructorMap.get(name);
        if (constructor != null && !verifyClassLoader(constructor)) {
            constructor = null;
            sConstructorMap.remove(name);
        }
        Class<? extends View> clazz = null;

        try {
            Trace.traceBegin(Trace.TRACE_TAG_VIEW, name);

            if (constructor == null) {
                // Class not found in the cache, see if it's real, and try to add it
                //1。加入的“android.view.”的前缀在此处就会用于查找Class对象
                clazz = mContext.getClassLoader().loadClass(
                        prefix != null ? (prefix + name) : name).asSubclass(View.class);

                if (mFilter != null && clazz != null) {
                    boolean allowed = mFilter.onLoadClass(clazz);
                    if (!allowed) {
                        failNotAllowed(name, prefix, attrs);
                    }
                }
                //2。构造函数没有缓存，则直接反射调用构造函数，并缓存起来
                constructor = clazz.getConstructor(mConstructorSignature);
                constructor.setAccessible(true);
                sConstructorMap.put(name, constructor);
            } else {
                // If we have a filter, apply it to cached constructor
                if (mFilter != null) {
                    // Have we seen this name before?
                    Boolean allowedState = mFilterMap.get(name);
                    if (allowedState == null) {
                        // New class -- remember whether it is allowed
                        clazz = mContext.getClassLoader().loadClass(
                                prefix != null ? (prefix + name) : name).asSubclass(View.class);

                        boolean allowed = clazz != null && mFilter.onLoadClass(clazz);
                        mFilterMap.put(name, allowed);
                        if (!allowed) {
                            failNotAllowed(name, prefix, attrs);
                        }
                    } else if (allowedState.equals(Boolean.FALSE)) {
                        failNotAllowed(name, prefix, attrs);
                    }
                }
            }

            Object lastContext = mConstructorArgs[0];
            if (mConstructorArgs[0] == null) {
                // Fill in the context if not already within inflation.
                mConstructorArgs[0] = mContext;
            }
            Object[] args = mConstructorArgs;
            args[1] = attrs;
            //3。利用反射构造函数，进行创建View
            final View view = constructor.newInstance(args);
            if (view instanceof ViewStub) {
                // Use the same context when inflating ViewStub later.
                final ViewStub viewStub = (ViewStub) view;
                //ViewStub会设置inflater
                viewStub.setLayoutInflater(cloneInContext((Context) args[0]));
            }
            mConstructorArgs[0] = lastContext;
            return view;

        } catch (NoSuchMethodException e) {
            final InflateException ie = new InflateException(attrs.getPositionDescription()
                    + ": Error inflating class " + (prefix != null ? (prefix + name) : name), e);
            ie.setStackTrace(EMPTY_STACK_TRACE);
            throw ie;

        } catch (ClassCastException e) {
            // If loaded class is not a View subclass
            final InflateException ie = new InflateException(attrs.getPositionDescription()
                    + ": Class is not a View " + (prefix != null ? (prefix + name) : name), e);
            ie.setStackTrace(EMPTY_STACK_TRACE);
            throw ie;
        } catch (ClassNotFoundException e) {
            // If loadClass fails, we should propagate the exception.
            throw e;
        } catch (Exception e) {
            final InflateException ie = new InflateException(
                    attrs.getPositionDescription() + ": Error inflating class "
                            + (clazz == null ? "<unknown>" : clazz.getName()), e);
            ie.setStackTrace(EMPTY_STACK_TRACE);
            throw ie;
        } finally {
            Trace.traceEnd(Trace.TRACE_TAG_VIEW);
        }
    }
```
这个方法还是比较简单的，首先在**注释1**处我们会发现我们刚才加入的"android.view."的前缀会加入到class到**全类名**中，用于查找Class对象。
紧接着在**注释2**其实LayoutInflater查找缓存中的构造器对象，避免频繁的调用反射来查找使用构造器函数。
```
private static final HashMap<String, Constructor<? extends View>> sConstructorMap =
            new HashMap<String, Constructor<? extends View>>();
```
可以看到这里就是一个类名作为key，构造器函数作为value的`hashMap`。
最后在**注释3**处通过反射调用View的构造函数，实现View的创建。
```
final View view = constructor.newInstance(args);
```

### 总结
到此关于LayoutInflater的源码分析算是有了一个整体的认识，通过分析`inflate`方法我们其实不仅仅可以学习关于加载布局时`root`和`attachToRoot`的关系，还可以了解到关于`include`标签，`merge`标签，的使用规则。当然我们最终会发现其实LayoutInflater的实质就递归解析，解析到类名后，如果是自定义的则是全类名，系统的则自动加上“android.view.”前缀，然后通过反射调用该类的构造函数，最终创建出View。
下一篇博客会继续分析关于LayoutInflater中关于工厂的使用，通过分析我们会发现关于`fragment`标签在系统的解析方式（本篇没有发现源码中有关于fragment标签的踪迹）。





