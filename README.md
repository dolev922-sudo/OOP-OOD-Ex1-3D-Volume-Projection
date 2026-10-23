# OOP-OOD-Ex1: 3D Volume Projection

A project that converts 3D medical imaging data (NRRD files) into 2D images and combines them into an MP4 video.

## 📌 Problem Definition

Medical scans, such as MRI and CT, store images as 3D volumes made up of small units called **voxels**.

Most visualization tools display 2D slices along the X, Y, or Z axes. The goal of this project is to extract a 2D image from **any given plane**, including planes that are not aligned with these axes.

The program receives:
- **NRRD file:** A 3D volume containing voxel values.
- **CSV file:** A list of planes, each defined by 3 or 4 points in 3D space.
- **Output:** An MP4 video containing one 2D image for each plane, in the order given in the CSV file.

## 🎯 Project Scope

The main focus is on **Object-Oriented Design (OOD)**, code quality, correctness, and efficient processing.

### In Scope

- **NRRD Loading:** Read 3D volumetric data from NRRD files.
- **Plane Validation:** Check that the given points form a valid triangle or trapezoid, using a tolerance of 0.001.
- **2D Projection:** Extract voxel values along the given plane and convert them into a 2D image.
- **Boundary Handling:** Use a value of 0 for points outside the 3D volume.
- **Video Creation:** Combine the generated images into an MP4 video.
- **Performance:** Support at least 30 FPS, with a target of 100+ FPS for a 500³-byte volume.
- **Command-Line Interface:** Run the program using:

```bash
  python Ex0.py <file.nrrd> <file.csv> <file.mp4>
```

### Out of Scope

- Interactive 3D visualization or graphical user interfaces.
- Editing or modifying the original NRRD data.
- Curved or non-planar projections.

## ⚙️ How It Works

1. Load the 3D volume from the NRRD file.
2. Read the plane coordinates from the CSV file.
3. Validate the plane's geometry.
4. Sample voxel values along the plane to create a 2D image.
5. Repeat for every plane in the CSV file.
6. Combine the images into an MP4 video.

    ## Documentation

- [Software Requirements Specification (SRS)](SRS.md)

The projection algorithm supports planes defined by either **3 points (isosceles triangle)** or **4 points (isosceles trapezoid)**.
