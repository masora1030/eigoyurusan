# eigoyurusan

English is too difficult for me.

Free software: MIT license

## Installation

### Stable release

To install eigoyurusan, run this command in your terminal:

```
$ pip install eigoyurusan
```

This is the preferred method to install eigoyurusan, as it will always install the most recent stable release.

If you don't have [pip](https://pip.pypa.io) installed, this Python [installation guide](http://docs.python-guide.org/en/latest/starting/installation/) can guide
you through the process.

### From sources

The sources for eigoyurusan can be downloaded from my [Github repo](https://github.com/masora1030/eigoyurusan)

You can either clone the public repository:

```
$ git clone git://github.com/masora1030/eigoyurusan
```

Once you have a copy of the source, you can install it with:

```
$ python setup.py install
```

## Usage

If you want to translate arXiv paper (you know it's link), please type a command like follow:

```
$ eigoyurusan -u https://arxiv.org/abs/XXXXXXXX
```

Other, If you want to translate your PDF file, please type a command like follow:

```
$ eigoyurusan -p hoge.pdf
```

If you want to translate to a language except Japanese, type a command like follows:

```
$ eigoyurusan -u https://arxiv.org/abs/XXXXXXXX -l RU
```

-l option sets a language. The details about the correspondence is as follows.

 - 'RU' : Russian
 - 'PL' : Polish
 - 'NL' : Dutch
 - 'IT' : Italian
 - 'PT' : Portuguese
 - 'ES' : Spanish
 - 'FR' : French
 - 'DE' : German


Use --small option, a quick, but not complete, summary is output on the command prompt:

```
$ eigoyurusan -u https://arxiv.org/abs/XXXXXXXX --small
```

