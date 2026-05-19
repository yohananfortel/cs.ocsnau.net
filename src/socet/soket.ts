import { io } from 'socket.io-client'


const socket = io('http://192.168.88.33:3000/')

export default socket

