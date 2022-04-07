
## Sounds

### Adding new sounds
New sounds are welcomed, both to **add** different sounds or to **replace** the existing ones to improve them.

Before adding them, the soundclips must pass a criterion:
* **Appropiate license:** their licenses must let us use the clip. Those are licenses such as `CC BY (SA)` and `CC0`. If the sound is yours, there's no problem; we will always inform the authorship.
* **Technical criterion:** explained below. You can measure and fit the sounds by yourself or let us do it for you; open an [issue](https://github.com/rafaelmardojai/blanket/issues) for this.
* **Ogg Vorbis format**

### Technical Criterion
As explained in [#20](https://github.com/rafaelmardojai/blanket/issues/20#issue-693420740), there are some psychoacoustic parameters that **all** sounds should fit in to be comfortable as ambient sounds.
Here is a table with the orientative values:

| Criteria    | LUFS (Int.) | Range | True Peak (dBTP) | Max LUFS
| :-:         | :-:         |  :-:  | :-:              | :-:
| Minimum     | -35         | 5-7   | -30              | -30
| Ideal       | -27         | 7-🔝  | -7,5             | -25
| Maximum     | -23         | 🔝    | -6               | -18

The parameters ordered according to their priority:

1. Range
2. LUFS Integrated
3. Maximum LUFS
4. True Peak

### How to measure
To measure the sound levels, all faders (sound-level bars) **must** be to the 100%. The most times this will be the loudest, unless it is indicated with percentage or with a mark of 0 dB.
`0 dB = 100%`

After setting app the faders, the sound source must be connected to an analyzer:
* I use [x42 Meter Collection](http://x42-plugins.com/x42/x42-meters#EBUr128), open source, allongside [Carla](https://kx.studio/Applications:Carla).
* Another good method to measure is using [Ardour](https://ardour.org) and its _Loudness Analysis_.

### How to fit
* **The Range** can **not** be changed upwards. If your clip does not fit in the Technical Criterion, you can send the clip to [porrumentzio@riseup.net](mailto:porrumentzio@riseup.net) explaining the situation, **only** if the range is bigger than 3,5.
* **LUFS Int.** and **Max. LUFS** can be modified changing the clip's **gain** (volume). The change on dBs is approximated to LUFS, so fit and analyze until you have it 😄
* **True Peak** tends to be some very-short-in-time transients, peaks. For fitting those peaks to about at least -6 dBs, use a **limiter** with the _threshold_ a bit more than -6 and short _release times_ (<5 ms).

### Where to put the soundclips
The soundclips are all under [`data/resources/sounds`](https://github.com/rafaelmardojai/blanket/tree/master/data/resources/sounds) directory with `.ogg` file extension, `Ogg Vorbis` encoding format.
If your sounds passed the criterion, you can add the sounds in your cloned local repo, at the specified directory, and the Pull Request to the main repository. _Open an issue if you don't know how to do this._

### Icons
Sounds must have a hair-style symbolic icon. 

If you don't have an icon and your sound has been aproved, you can wait for someone in the communty to contribute one. But no sound will be included in the app without a proper icon.
_______
_More documentation here:_ [**Sounds_documentation.md**](https://github.com/rafaelmardojai/blanket/blob/master/doc/Sound_documentation.md)
