# Compatibility shim for newer Ruby versions.
# Liquid 4 in Jekyll 3.9 still expects `tainted?`/`untaint`.
class Object
  unless method_defined?(:tainted?)
    def tainted?
      false
    end
  end

  unless method_defined?(:untaint)
    def untaint
      self
    end
  end
end
