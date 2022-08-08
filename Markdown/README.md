# Markdown
> Markdown의 기본적인 개념과 문법 등을 설명하고, Sample Markdown file을 통해 결과를 확인

### Index :
1. [__What is Markdown?__](#about_markdown)
2. [__Markdown Basic Grammar__](#basic_grammar_markdown)

# 1. What is Markdown? <a name="about_markdown" />
> Markdown의 기본적인 개념

Markdown은 __Text__ 기반의 _Markup Language_ 로, 쉽게 쓰고 읽을 수 있으며, HTML 변환이 가능한 언어이다. 특수문자 및 문자를 이용해 매우 간단한 구조의 문법을 사용하여 Web에서도 빠르게 컨텐츠를 작성하고 직관적으로 인식할 수 있다. __Github__ 에 의해서 각광받기 시작했고, 다양한 곳에서 Markdown 기반의 페이지들이 나오고 있다.

- Markdown의 장점
  - 간결하다.
  - 별도의 도구가 없어도 작성할 수 있다.
  - 다양한 형태로 변환이 가능하다.
  - Text로 저장되기 때문에 용량이 적어 보관이 용이하다.
  - Supporting Program과 Platform이 다양하다.
  
- Markdown의 단점
  - 표준이 없다. 때문에, 도구에 따라서 변환 방식이나 생성물이 다르다.
  - 모든 HTML Markup을 대신하지 못한다.
  
# 2. Markdown Basic Grammar <a name="basic_grammar_markdown" />
> 기본적인 Markdown의 문법

### Font Control

- Font Size : H1 ~ H6까지 지원 (#으로 표현)

```
# H1 Size
## H2 Size
### H3 Size
...
```

- Font Accent : '_' 혹은 '*'을 통해 밑줄 혹은 굵게 표시한다.

sample : **This is Bold** and *This is Italic*

```
__Bold Font__
**Bold Font**

_Italic Font_
*Italic Font*
```

- 인용 구문(Blockquote) : '>'를 통해 인용을 나타낸다. (제목에 대한 간단한 부가 설명으로도 쓰인다.)

```
# This is Header 1
> This is BlockQuote...
>> BlockQuote 아래에 또 다른 BlockQuote
```

- List : 순서가 있는 목록 & 순서가 없는 목록 (번호. & '-')

순서가 있는 목록

```
어떤 번호를 입력해도 내림차순으로 Numbering이 이루어진다.
1. Number1
2. Number2
5. Number5 -> 실제로는 3. ...
```

순서가 없는 목록(-, *, +)

```
- 목차 1
  - 목차 2
    + 목차 3
    ...
```

- Code Block : Code를 넣을 수 있는 부분으로 언어에 맞게 Code 색을 변환해주기도 한다. (``` 사용)

```python
# Code Block은 ' ```Language' 를 통해서 언어에 맞게 변환한다.
def sum(a, b):
  return a + b
  
print(sum(5, 1))
```

Code Block에서 지원하는 언어 목록

|Language|Markdown|Language|Markdown|
|:--------:|:--------:|:--------:|:--------:|
|Bash|bash|JSON|json|
|C#|cs|Java|java|
|C++|cpp|JavaScript|javascript|
|CSS|css|PHP|php|
|Diff|diff|Perl|perl|
|HTML, XML|html|Python|python|
|HTTP|http|Ruby|ruby|
|Ini|ini|SQL|sql|
