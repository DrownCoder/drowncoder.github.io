---
title: "FragmentTransaction的add和Fragment的onCreateView()相关问题"
category: "Android基础"
category_slug: "android基础"
source_name: "FragmentTransaction的add和Fragment的onCreateView()相关问题"
sort_key: 0004
---
接着上一篇的博客遗留的问题，我查了许多资料，看了许多源码，终于经过三天的努力理解了这个问题。

现在先阐述一下问题，再同一个FragmentTransaction事务中，将一个已经存在的frag1通过remove()掉，再add()这个frag1后，再commit()提交事务，无法显示该fragment。（强调一下：是在同一个事务中）
**问题产生原因：**
有人可能会想，为啥要这么做，可能是因为我比较无聊，比较较真，我当时本来hide()后再show()就可以显示，但是由于不小心将hide()写成了remove()就引发了接下来一系列问题，我考虑的是既然remove()掉就再add()不就能显示了吗？这时候就出现了这个问题。
**解决问题过程：**

1.出现了上面的问题我第一个想法是是不是由于Fragment被remove后被销毁了，导致再add()，由于Fragment是null所以不能显示。
但是经过调试，我发现remove后指向Fragment的变量并不是null,这个时候我就纠结了，不是被销毁了吗，怎么不为null,所以我开始怀疑是不是没有被销毁。
但是，经过调试，我对Fragment重写了所有生命周期的方法，并且通过Tag进行显示下面是显示的图片
![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-f52342c7428d238b?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)  
可以看出，remove后Fragment确实执行了onDetach，也就是说这个Fragment的生命周期已经结束了，但是调试结果是这个Fragment确实不是为空，我就上论坛提问，几位大神的回答让我明白了这些
![](http://upload-images.jianshu.io/upload_images/7866586-7771f722b3a5d95a?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
没错，就像他们回答的一样，remove只是将和Activity解绑了，
![](http://upload-images.jianshu.io/upload_images/7866586-1f38f7dab09706e4?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
可以看到解绑后，这个Fragment的mActivity为null。所以这个想法就是错的。
2.第一个想法是错的，我就继续改，发现如果，frag1remove()再add()确实不显示，但是，如果从另一个frag2跳转到frag1,同样是执行的add()方法，这样就显示了，这我就更纠结了，同样的frag1,并没有操作修改他，同样的add()方法，怎么一个能显示，一个不能显示了哪？！
从这里想，我就开始找不同，也就是找变的因素，首先我对生命周期的方法进行了调试发现frag1在两次add()后都执行了
![这个是remove后立马add的frag的生命周期](http://upload-images.jianshu.io/upload_images/7866586-1eb5ec1ec53ab667?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
而第二种能显示的frag1也同样执行到了onResume，所以这样这期间Frag1并没有什么区别，但是无数次断点调试，无意间我发现了一个巨大的区别，**那就是在调用**
**onCreateView(LayoutInflater inflater,ViewGroup container,Bundle savedInstanceState)** **这个方法时，第一种不显示的情况container是null，而第二种container为FrameLayout。**

**找到不显示的根本原因了！container为空当然无法显示了**
3.基于第二步找到问题原因就开始想问题出现的原因，同样是transaction.add(R.id.content, f1);指定了父容器为啥一个container为null一个不是null哪？！，查阅了很多资料，看了Fragment的源码还有FragmentTransaction的源码，都没有找到原因，网上这块也没有发现有相关解释，终于我找到了一篇有关的解释：http://www.cnblogs.com/ttylinux/p/3775491.html
虽然这篇讲的和我这个没有太大关系，但是他的解释让我有了一定思路，尤其是**对官方关于该方法的解释** 让我有了一定想法，我去查询这块的源码，官方对oncreateview()的解释是这样的

```
 /**
     * Called to have the fragment instantiate its user interface view.
     * This is optional, and non-graphical fragments can return null (which
     * is the default implementation).  This will be called between
     * {@link #onCreate(Bundle)} and {@link #onActivityCreated(Bundle)}.
     * 
     * <p>If you return a View from here, you will later be called in
     * {@link #onDestroyView} when the view is being released.
     * 
     * @param inflater The LayoutInflater object that can be used to inflate
     * any views in the fragment,
     * @param container If non-null, this is the parent view that the fragment's
     * UI should be attached to.  The fragment should not add the view itself,
     * but this can be used to generate the LayoutParams of the view.
     * @param savedInstanceState If non-null, this fragment is being re-constructed
     * from a previous saved state as given here.
     * 
     * @return Return the View for the fragment's UI, or null.
     */
```
我读了很多遍，发现了一个地方**The fragment should not add the view itself** 意思是该fragment不应该添加视图本身，这个翻译虽然让人困惑，但是总能感觉出点什么**，fragment不能加自身，我一开始只有frag1,remove后再add()frag1是不是添加自身？**
**而我如果frag1remove后再add确实不显示，但是再add（）frag2,然后再把frag2hide()再把remove掉的frag1 add()就显示了**（这句话有点绕口，但是是关键思路），**确实两次调用的oncreateview（）时一个是从frag1remove后在add()frag1,一个是从frag2再add（）frag1**这不就印证了官方的话：The fragment should not add the view itself。
为了证实我的想法，我在同一个事务中，这是界面只有frag1,我remove掉后再add()一个一开始已经初始化好的frag2(frag2这是第一次被add),
这样从frag1add一个frag2,如果正确就能显示吧，结果是：正确！！！！
**总结：**
虽然这个问题其实很无聊，很蛋疼，没有什么意义，但也算一种解决问题的思路吧，一种思想吧，**总的来说就是不能从frag1->frag1,要从fragn->fragm(n!=m)**
还有，看源码有点意思。。。。。。
如有错误希望大家能够指出，这只是我自己的分析，不知道是不是有道理
