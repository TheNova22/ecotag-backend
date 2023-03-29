class Emission:

    @staticmethod
    def airEmission(distance):

        return 158 * distance

    @staticmethod
    def railEmission(distance):

        return 30 * distance


    @staticmethod
    def waterEmission(distance):

        return 2 * distance



    @staticmethod
    def roadEmission(distance):

        return 78 * distance
    