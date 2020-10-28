
## Disclaimer
This recommendations about sounds will be thought **for humans!** I suppose that this are the expected listeners of this application, but it is important to claim that this recommendations are **not** for **other animals**.

The standard and recommendations used here will be based on [**EBU R128**](https://tech.ebu.ch/publications/r128/), the standard of European Broadcast Union about audio normalisation and maximum sound levels.
The main unit used will be the LUFS, `Loudness Unit Full Scale`, which is a relative unit to humans hearing. More info [here](https://en.wikipedia.org/wiki/EBU_R_128#Specification).

## Characteristics
Here I'll explain each characteristic that should be taken into account to decide whether a soundclip is ideal for the app.

### LUFS Integrated
The **LUFS Integrated** is an average measure which a sound has through all its length. A soundclip does **not** have the same level at each moment, it changes. With this unit we can measure an average of the clip.

The closer to 0 LUFS, the louder. It is ***inverted***.

### Dynamic Range
A sound has a changing level through its duration. With the **dynamic range** we measure the range between the loudest and
the lowest level registered.
The **higher** the **range** (the difference between the loudest and lowest level), the **more comfortable** the sound will be. Sounds with **poor range exhaust** the listener and, therefore, **annoys**.

This characteristic is almost the most important in ambient sounds, as what we want is to be comfortable, not annoying.

### True Peak (dBTP)
This is the **maximum** level that the sound wave takes through the duration of itself. This is **imperceptible** because this maximum level lasts only **milliseconds**. But having too loud peaks produces annoying clipping (snaps, cracks, pops) and distorted sounds on speakers, so it is better to avoid having them.

### Max LUFS (momentary)
This, unlike True Peak, is a **more perceptible** way to meter **maximum** loudness, as it meters it in a timeframe of 400ms. 

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


## Recommendations

* The **longest** the **recording**, possibly the more **comfortable**. Sounds in nature vary a lot, they tend to have large dynamic ranges.
* **Lower** sound levels, specially for those monotonous soundclips.
* Avoid short and [sausage](https://cnet3.cbsistatic.com/img/_EPvPKH6Fg7edW0NeuHUuJ6X0lQ=/2011/07/06/2f50c706-fdc2-11e2-8c7c-d4ae52e62bcc/Arcade_Fire_Ready_to_Start.jpg) clips.

### Criterion that every clip should pass
As the maximum comfortable perceived level is directly correlated to the range, there could be variations, but here is a table:
| Criterion | LUFS (Int.) | Range | True Peak (dBTP) | Max LUFS
| :-:       | :-:         |  :-:  | :-:              | :-:
| Minimum   | -35         | 5-7   | -30              | -30
| Ideal     | -27         | 7-🔝  | -7,5             | -25
| Maximum   | -23         | 🔝    | -6               | -18

_________

## Made changes
**New sounds:**
| Sound                                                         | App version | Author   | License  | LUFS (Int.) | Range | True Peak (dBTP) | Modifications
| :-:                                                           | :-:         | :-:      | :-:      | :-:         | :-:   | :-:              |  :-:
| [Waves](https://freesound.org/people/Luftrum/sounds/48412/)   | `4.0`       | Luftrum  | CC BY    | -23         | 9,8   | -0,4             | -2,5 dB & Lim -6,5 dB : 2,5 ms 
| [Birds](https://freesound.org/people/kvgarlic/sounds/156826/) | `4.0`       | kvgarlic | CC0      | -39,8       | 16,4  | -24,4            | +12 dB
| [Train](https://trains.ambient-mixer.com/rainy-train)         | `4.0`       | vahid    | CC Sampling + | -27    | 8,7   | -8,1             | None
| [Stream](https://freesound.org/people/gluckose/sounds/333987/) | `4.0`      | gluckose | CC0      | -39,2       | 1     | -15,7            | None
| [Boat](https://freesound.org/people/Falcet/sounds/439365/)    | `4.0`       | Falcet   | CC0      | -50,5       | 6,6   | -26              | +20 dB
| [City](ttps://freesound.org/people/gezortenplotz/sounds/44796/) | `4.0`   | gezortenplotz | CC BY | -38,7       | 4     | -18,9            | +11 dB

**Replaced sounds:**
| Sound                                                         | App version | Author    | License  | LUFS (Int.) | Range | True Peak (dBTP) | Modifications
| :-:                                                           | :-:         | :-:       | :-:      | :-:         | :-:   | :-:              |  :-:
| [Rain](https://freesound.org/people/alex36917/sounds/524605/) | `4.0`       | alex36917 | CC BY    | -29,3       | 4,6   | 0                | +2 dB & Lim -6,1 dB : 3,2 ms

**Modified sounds:**
| Sound   | App version | Author         | License  | LUFS (Int.) | Range | True Peak (dBTP) | Modifications | Needs replacement
| :-:     | :-:         | :-:            | :-:      | :-:         | :-:   | :-:              |  :-:          | :-:
| Storm   | `4.0`       | Digifish music | Unknown  | -17,9       | 9,7   | 0                | -7 dB         |
| Pink noise | `4.0`    | Omegatron      | Unknown  | -11,7       | 4,8   | -0,7             | -10 dB        | X [#11](https://github.com/rafaelmardojai/blanket/issues/11)
| Summer night | `4.0`  | Unknown        | Unknown  | -14,4       | 2,7   | -3,4             | -12 dB        | X
| White noise | `4.0`   | Jorge Stolfi   | Unknown  | -1,1        | 1,8   | 4,6              | -25 dB        | X [#11](https://github.com/rafaelmardojai/blanket/issues/11)
| Wind    | `4.0`       | Stilgar        | Unknown  | -16,6       | 0     | -3,1             | -6 dB         | X

## Needs replacement
**For `4.0`**
* Wind
* Summer night
* Coffee Shop
* Fireplace
* Pink noise
* White noise
