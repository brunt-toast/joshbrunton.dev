## Manhattan Distance

Manhattan distance is a computationally cheap algorithm for determining the distance between 2 points in a Cartesian co-ordinate system, such as RGB colour space. 

It's also known as: 
* Taxicab distance
* City block distance
* Rectilinear distance
* L1 distance

Unlike Euclidean distance, which is the length of a line segment between 2 points (often termed "as the crow flies"), Manhattan distance is the sum of absolute differences of the co-ordinates. 

![](https://cmdlinetips.com/wp-content/uploads/2022/12/Manhattan_distance.png)

The distance between points $p$ and $q$ in an $n$-dimensional Cartesian co-ordinate system, where $p=(p_1,p_2...p_n)$ and $q=(q_1,q_2...q_n)$, is: 

$$
d_T(p,q) = ||p - q||_T = \sum_{i=1}^{n}|p_i-q_i|
$$

This is one of the fastest options for computing the visual similarity of two colours, but yields the least accurate results due to the limitations of the algorithm and the fact that the RGB colour space is not perceptually uniform. We can improve upon this by using a more fitting algorithm. 

## Euclidean Distance 

Euclidean distance, as previously mentioned, is the length of the line segment between two points in a Cartesian co-ordinate system. 

Its implementation differs slightly based on the number of dimensions. Since RGB is a 3-dimensional space, we use: 

$$
d(p,q) = \sqrt{(p_1-q_1)^2 + (p_2-q_2)^2 + (p_3-q_3)^2}
$$

This is a little more computationally expensive and a little more accurate than Manhattan distance, but still relatively inaccurate because of the non-uniformity of the colour space. 

There are several adjustments upon this algorithm which attempt to introduce weights, however the improvements are minimal. What we really need is to change the colour space we're using. 

## CIE76 

In 1976, the Commission Internationale de L'Éclairage attempted to define a more perceptually uniform colour space. They came up with LAB (or CIELab), expresses colour in terms of Lightness ($L$), green/red spectrum ($a$), and blue/yellow spectrum ($b$). 

The CIE76 colour difference formula is simply the application of the Euclidean distance algorithm to two $L*a*b*$ co-ordinates: 

$$
\Delta E^{*}_{ab} = \sqrt{(L^*_2-L^*_1)^2 + (a^*_2-a^*_1)^2 + (b^*_2-b^*_1)^2}
$$

Research has shown that a $\Delta E^*_{ab}$ of around 2.3 is a "just noticeable difference". 

Unfortunately, due to limitations in the CIELab colour space, this algorithm performs more poorly in blue, gray, and low-chroma (saturation) regions. 

## CIE94

In 1994, the CIE improved upon the CIE76 algorithm in an attempt to address non-uniformities. They introduced some weight parameters $k_L$, $k_C$ and $k_H$. 

For graphic arts, the parameters are:

$$
k_L = 1 \\
K_1 = 0.045 \\
K_" = 0.015
$$

For textile arts, they are: 

$$
k_L = 2 \\
K_1 = 0.048 \\
K_" = 0.014
$$

The final algorithm also relies on the following functions: 

$$
C^*_n = \sqrt{{a^*_n}^2 + {b^*_n}^2} \\
\Delta H* = \sqrt{{\Delta E^*_{ab}}^2 - \Delta L^{*2} - \Delta C^{*2}} = \sqrt{\Delta a^{*2} + \Delta b^{*2} - \Delta C^{*2}} \\
S_L = 1 \\
S_C = 1 + K_1C^*_1 \\
S_H = 1 + K_2C^*_1

$$

With all that set up, difference between colours $(L^*_1, a^*_1, b^*_1)$ and $(L^*_2, a^*_2, b^*_2)$ is defined as: 

$$
\Delta E^*_{94} = \sqrt{({{\Delta L*}\over{k_LS_L}})^2 + ({{\Delta C*}\over{k_CS_C}})^2 + ({{\Delta L*}\over{k_HS_H}})^2}
$$

While this was better than CIE74, it still retained the problems with blue, grey, and low-chroma regions. 

## CIEDE2000 

Since CIE94 didn't fully resolve the perceptual uniformity issue, the CIE published CIEDE2000 in 2001. They added hue rotation $R_T$ to compensate for the blue region, and 