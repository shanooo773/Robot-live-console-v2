import { createContext, useContext, useState } from "react"
import type { ReactNode } from "react"

interface Booking {
  sessionType: string
  date: string
  time: string
  duration: string
}

interface StatsType {
  activeSessions: number
  completedSimulations: number
  robotsUsed: number
  labHours: number
}

interface Robot {
  name: string
  status: "online" | "idle" | "offline"
}

interface ActivityItem {
  id: number
  message: string
  time: string
}

interface AppContextType {

  /* AUTH */
  isAuthenticated: boolean
  login: () => void
  logout: () => void

  /* BOOKING */
  booking: Booking | null
  setBooking: (booking: Booking) => void

  /* STATS */
  stats: StatsType
  setStats: React.Dispatch<React.SetStateAction<StatsType>>

  /* ROBOTS */
  robots: Robot[]

  /* ACTIVITY */
  activity: ActivityItem[]
  addActivity: (msg: string) => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export const AppProvider = ({ children }: { children: ReactNode }) => {

  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const [booking, setBookingState] = useState<Booking | null>(null)

  const [stats, setStats] = useState<StatsType>({
    activeSessions: 0,
    completedSimulations: 0,
    robotsUsed: 0,
    labHours: 0
  })

  const [activity, setActivity] = useState<ActivityItem[]>([])

  const robots: Robot[] = [
    { name: "TurtleBot3", status: "online" },
    { name: "Robotic Arm", status: "idle" },
    { name: "Autonomous Rover", status: "offline" }
  ]

  /* AUTH FUNCTIONS */

  const login = () => {
    setIsAuthenticated(true)
  }

  const logout = () => {
    setIsAuthenticated(false)
  }

  /* ACTIVITY */

  const addActivity = (msg: string) => {

    const newActivity: ActivityItem = {
      id: Date.now(),
      message: msg,
      time: new Date().toLocaleTimeString()
    }

    setActivity(prev => [newActivity, ...prev])
  }

  /* BOOKING */

  const setBooking = (newBooking: Booking) => {

    setBookingState(newBooking)

    setStats(prev => ({
      ...prev,
      activeSessions: prev.activeSessions + 1
    }))

    addActivity("New robotics session booked")
  }

  return (

    <AppContext.Provider
      value={{

        isAuthenticated,
        login,
        logout,

        booking,
        setBooking,

        stats,
        setStats,

        robots,

        activity,
        addActivity
      }}
    >

      {children}

    </AppContext.Provider>

  )
}

export const useAppContext = () => {

  const context = useContext(AppContext)

  if (!context) {
    throw new Error("useAppContext must be used inside AppProvider")
  }

  return context
}