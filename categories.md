---
layout: default
title: 分类
permalink: /categories/
---
{% assign groups = site.articles | group_by: "category" | sort: "name" %}

<section class="panel">
  <div class="section-heading">
    <h1>分类</h1>
    <p>按旧博客目录整理，方便继续维护。</p>
  </div>

  {% for group in groups %}
    <section class="category-block" id="{{ group.items.first.category_slug }}">
      <h2>{{ group.name }}</h2>
      <div class="article-list">
        {% assign items = group.items | sort: "sort_key" %}
        {% for article in items %}
          <article class="article-card compact">
            <p class="meta">{{ article.source_name }}</p>
            <h3><a href="{{ article.url | relative_url }}">{{ article.title }}</a></h3>
          </article>
        {% endfor %}
      </div>
    </section>
  {% endfor %}
</section>
