import cv2
import numpy as np
import pytesseract
import traceback

class image2recorte():
    def __init__(self):
        pass

    def ordenar_puntos(self, pts):
        # Convertir a un array 2D normal si es necesario
        pts = pts.reshape(4, 2)
        # Ordenar por suma (x + y) para identificar esquinas
        suma = pts.sum(axis=1)
        diferencia = np.diff(pts, axis=1)
        # Superior izquierdo: menor suma
        punto_sup_izq = pts[np.argmin(suma)]
        # Inferior derecho: mayor suma
        punto_inf_der = pts[np.argmax(suma)]
        # Superior derecho: menor diferencia (x - y)
        punto_sup_der = pts[np.argmin(diferencia)]
        # Inferior izquierdo: mayor diferencia (x - y)
        punto_inf_izq = pts[np.argmax(diferencia)]
        return np.array([punto_sup_izq, punto_sup_der, punto_inf_izq, punto_inf_der], dtype=np.float32)

    def obtener_recorte(self, frame: np.ndarray, log_level=0):
        try:
            if not isinstance(frame, np.ndarray):
                raise ValueError("El parámetro de entrada debe ser una imagen de OpenCV (numpy.ndarray).")

            copy_image = frame.copy()
            detected_color = None
            hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  

            # Mostrar la imagen HSV
            if log_level == 1:
                cv2.imshow('HSV Image', hsv_image)

            # Definir el rango para el color azul
            lower_blue = np.array([100, 150, 50])
            upper_blue = np.array([140, 255, 255])
            lower_red_1 = np.array([0, 50, 50])
            upper_red_1 = np.array([10, 255, 255])
            lower_red_2 = np.array([170, 50, 50])
            upper_red_2 = np.array([180, 255, 255])

            # Crear máscaras para azul y rojo
            mask_blue = cv2.inRange(hsv_image, lower_blue, upper_blue)
            mask_red_1 = cv2.inRange(hsv_image, lower_red_1, upper_red_1)
            mask_red_2 = cv2.inRange(hsv_image, lower_red_2, upper_red_2)
            mask_red = cv2.bitwise_or(mask_red_1, mask_red_2)
            combined_mask = cv2.bitwise_or(mask_blue, mask_red)

            if log_level == 1:
                cv2.imshow('Combined Mask', combined_mask)

            # Tratamiento morfológico
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            closed_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
            cleaned_mask = cv2.morphologyEx(closed_mask, cv2.MORPH_OPEN, kernel)

            if log_level == 1:
                cv2.imshow('Cleaned Mask', cleaned_mask)

            contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            vertices = []

            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    if area > 500:
                        x, y, w, h = cv2.boundingRect(approx)
                        aspect_ratio = float(w) / float(h)
                        if 0.8 < aspect_ratio < 1.2:
                            angles = []
                            for i in range(4):
                                pt1 = approx[i][0]
                                pt2 = approx[(i + 1) % 4][0]
                                pt3 = approx[(i + 2) % 4][0]
                                v1 = np.array([pt1[0] - pt2[0], pt1[1] - pt2[1]])
                                v2 = np.array([pt3[0] - pt2[0], pt3[1] - pt2[1]])
                                angle = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0))
                                angle_deg = np.degrees(angle)
                                angles.append(angle_deg)

                            if all(80 < angle < 100 for angle in angles):
                                cv2.drawContours(copy_image, [approx], -1, (0, 255, 0), 3)
                                for point in approx:
                                    x, y = point[0]
                                    cv2.circle(copy_image, (x, y), 5, (0, 0, 255), -1)
                                vertices = approx

            if log_level == 1:
                cv2.imshow('Detected Squares', copy_image)
            # print(vertices)
            if len(vertices) == 0:
                if(log_level):
                    print("No se detectó un cuadrado.")
                return None

            puntos_origen = np.array([vertices[2][0], vertices[3][0], vertices[0][0], vertices[1][0]], np.float32)
            puntos_origen = self.ordenar_puntos(puntos_origen)

            mask_black = np.zeros_like(frame)
            cv2.fillPoly(mask_black, [vertices], (255, 255, 255))
            result = cv2.bitwise_and(frame, mask_black)

            if log_level == 1:
                cv2.imshow('Masked Region', result)

            ancho = 100
            alto = 100
            puntos_destino = np.float32([[0, 0], [ancho, 0], [0, alto], [ancho, alto]])
            matriz = cv2.getPerspectiveTransform(puntos_origen, puntos_destino)
            numero_cuadrado = cv2.warpPerspective(result, matriz, (ancho, alto))
            # numero_bin = cv2.warpPerspective(result, matriz, (ancho, alto))
            if log_level == 1:
                cv2.imshow('Corrected Image', numero_cuadrado)

            return numero_cuadrado

        except Exception as e:
            print(f"Ocurrió un error: {e}")
            print("Error en la línea:", traceback.format_exc())
            return None
