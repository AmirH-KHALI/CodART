public abstract class Shape {
    public int x = 12, y = 12;
    abstract void area();
    public abstract int[] center();
}

interface test {
    int[] center();
}

class circle extends Shape {

    public void area() {
        System.out.println("area");
    }

    public int[] center() {
        return new int[]{0, 0};
    }
}